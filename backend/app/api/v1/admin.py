from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from backend.app.core.deps import get_current_admin, get_db, has_admin_access
from backend.app.core.password import hash_password
from backend.app.models.item import Item
from backend.app.models.match import Match
from backend.app.models.message import Message
from backend.app.models.notification import Notification
from backend.app.models.user import User
from backend.app.schemas.admin import AdminUserOut, AdminUserUpdate, StatsOverview

router = APIRouter(prefix='/admin', tags=['管理员'])


def get_user_or_404(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail='用户不存在')
    return user


def get_item_or_404(db: Session, item_id: int) -> Item:
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail='物品不存在')
    return item


def ensure_user_manageable(current_admin: User, target_user: User) -> None:
    if target_user.id == current_admin.id:
        raise HTTPException(status_code=400, detail='不能操作自己的账号')

    target_is_admin = has_admin_access(target_user)
    if target_user.is_superadmin and not current_admin.is_superadmin:
        raise HTTPException(status_code=403, detail='普通管理员不能操作超级管理员账号')
    if target_is_admin and not current_admin.is_superadmin:
        raise HTTPException(status_code=403, detail='普通管理员不能操作其他管理员账号')


@router.get('/users', response_model=List[AdminUserOut], summary='获取用户列表')
def list_users(
    keyword: Optional[str] = Query(None, description='按用户名或联系方式搜索'),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    query = db.query(User)
    if keyword:
        query = query.filter(User.username.contains(keyword) | User.contact.contains(keyword))
    return query.order_by(User.id.asc()).offset((page - 1) * page_size).limit(page_size).all()


@router.get('/users/{user_id}', response_model=AdminUserOut, summary='获取用户详情')
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return get_user_or_404(db, user_id)


@router.delete('/users/{user_id}', status_code=204, summary='删除用户')
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    user = get_user_or_404(db, user_id)
    ensure_user_manageable(current_admin, user)
    db.delete(user)
    db.commit()


@router.patch('/users/{user_id}', response_model=AdminUserOut, summary='修改用户状态和权限')
def update_user(
    user_id: int,
    payload: AdminUserUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    user = get_user_or_404(db, user_id)
    ensure_user_manageable(current_admin, user)

    if payload.is_active is not None:
        user.is_active = payload.is_active

    role_change_requested = payload.is_admin is not None or payload.is_superadmin is not None
    if role_change_requested and not current_admin.is_superadmin:
        raise HTTPException(status_code=403, detail='只有超级管理员可以调整管理员权限')

    if payload.is_superadmin is not None:
        user.is_superadmin = payload.is_superadmin
        if payload.is_superadmin:
            user.is_admin = True

    if payload.is_admin is not None:
        if user.is_superadmin and payload.is_admin is False:
            raise HTTPException(status_code=400, detail='超级管理员必须保留管理员权限')
        user.is_admin = payload.is_admin
        if payload.is_admin is False:
            user.is_superadmin = False

    if payload.new_password:
        user.password_hash = hash_password(payload.new_password)

    db.commit()
    db.refresh(user)
    return user


@router.get('/items', summary='获取物品列表（含下架/删除记录）')
def list_all_items(
    type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    is_deleted: Optional[bool] = Query(None, description='True=已下架，False=正常'),
    record_state: Optional[str] = Query(None, description='in_progress/completed/off_shelf/deleted'),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    query = db.query(Item)
    if type:
        query = query.filter(Item.type == type)
    if status:
        query = query.filter(Item.status == status)
        if status in ('pending', 'matched', 'closed'):
            query = query.filter(
                Item.is_deleted.is_(False),
                Item.owner_deleted.is_(False),
            )
    if is_deleted is not None:
        query = query.filter(Item.is_deleted == is_deleted)
    if record_state in ('active', 'in_progress'):
        query = query.filter(
            Item.is_deleted.is_(False),
            Item.owner_deleted.is_(False),
            Item.status.in_(['pending', 'matched']),
        )
    elif record_state == 'completed':
        query = query.filter(
            Item.is_deleted.is_(False),
            Item.owner_deleted.is_(False),
            Item.status == 'closed',
        )
    elif record_state == 'off_shelf':
        query = query.filter(
            Item.is_deleted.is_(True),
            Item.owner_deleted.is_(False),
        )
    elif record_state == 'deleted':
        query = query.filter(Item.owner_deleted.is_(True))
    if keyword:
        query = query.filter(Item.title.contains(keyword) | Item.description.contains(keyword))

    total = query.count()
    items = query.order_by(Item.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        'total': total,
        'items': [
            {
                'id': item.id,
                'type': item.type,
                'title': item.title,
                'category': item.category,
                'status': item.status,
                'is_deleted': item.is_deleted,
                'owner_deleted': getattr(item, 'owner_deleted', False),
                'record_state': (
                    'deleted'
                    if getattr(item, 'owner_deleted', False)
                    else 'off_shelf'
                    if item.is_deleted
                    else 'completed'
                    if item.status == 'closed'
                    else 'in_progress'
                ),
                'owner_id': item.owner_id,
                'owner_username': item.owner.username if item.owner else None,
                'created_at': item.created_at,
            }
            for item in items
        ],
    }


@router.delete('/items/{item_id}', status_code=204, summary='管理员下架物品')
def admin_delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    item = get_item_or_404(db, item_id)
    item.is_deleted = True
    db.commit()


@router.delete('/items/{item_id}/hard', status_code=204, summary='管理员彻底删除物品')
def admin_hard_delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    item = get_item_or_404(db, item_id)

    db.query(Message).filter(Message.item_id == item.id).delete(synchronize_session=False)
    db.query(Notification).filter(Notification.related_item_id == item.id).delete(synchronize_session=False)
    db.query(Match).filter(
        (Match.lost_item_id == item.id) | (Match.found_item_id == item.id)
    ).delete(synchronize_session=False)
    db.delete(item)
    db.commit()


@router.patch('/items/{item_id}/restore', summary='管理员恢复已下架物品')
def admin_restore_item(
    item_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    item = get_item_or_404(db, item_id)
    item.is_deleted = False
    item.owner_deleted = False
    db.commit()
    return {'message': '物品已恢复'}


@router.patch('/items/{item_id}/status', summary='管理员修改物品状态')
def admin_update_item_status(
    item_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    status = payload.get('status')
    if status not in ('pending', 'matched', 'closed'):
        raise HTTPException(status_code=400, detail='无效状态，可选：pending / matched / closed')
    item = get_item_or_404(db, item_id)
    item.status = status
    db.commit()
    return {'message': '状态已更新', 'status': status}


@router.get('/stats', response_model=StatsOverview, summary='系统统计概览')
def get_stats(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active.is_(True)).count()

    total_items = db.query(Item).filter(Item.is_deleted.is_(False), Item.owner_deleted.is_(False)).count()
    lost_items = db.query(Item).filter(Item.type == 'lost', Item.is_deleted.is_(False), Item.owner_deleted.is_(False)).count()
    found_items = db.query(Item).filter(Item.type == 'found', Item.is_deleted.is_(False), Item.owner_deleted.is_(False)).count()
    matched_items = db.query(Item).filter(Item.status == 'matched', Item.is_deleted.is_(False), Item.owner_deleted.is_(False)).count()
    pending_items = db.query(Item).filter(Item.status == 'pending', Item.is_deleted.is_(False), Item.owner_deleted.is_(False)).count()

    total_matches = db.query(Match).count()
    confirmed_matches = db.query(Match).filter(Match.status == 'confirmed').count()

    total_notifications = db.query(Notification).count()
    unread_notifications = db.query(Notification).filter(Notification.is_read.is_(False)).count()

    return StatsOverview(
        total_users=total_users,
        active_users=active_users,
        total_items=total_items,
        lost_items=lost_items,
        found_items=found_items,
        matched_items=matched_items,
        pending_items=pending_items,
        total_matches=total_matches,
        confirmed_matches=confirmed_matches,
        total_notifications=total_notifications,
        unread_notifications=unread_notifications,
    )


@router.get('/stats/category', summary='各类别物品数量统计')
def get_category_stats(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    rows = (
        db.query(Item.category, func.count(Item.id).label('count'))
        .filter(Item.is_deleted.is_(False), Item.owner_deleted.is_(False), Item.category.isnot(None))
        .group_by(Item.category)
        .order_by(func.count(Item.id).desc())
        .all()
    )
    return {'categories': [{'category': row.category, 'count': row.count} for row in rows]}


@router.get('/stats/daily', summary='近30天每日发布量统计')
def get_daily_stats(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    since = datetime.utcnow() - timedelta(days=30)
    rows = (
        db.query(
            func.date(Item.created_at).label('date'),
            Item.type,
            func.count(Item.id).label('count'),
        )
        .filter(Item.created_at >= since, Item.is_deleted.is_(False), Item.owner_deleted.is_(False))
        .group_by(func.date(Item.created_at), Item.type)
        .order_by(func.date(Item.created_at))
        .all()
    )
    return {'daily': [{'date': str(row.date), 'type': row.type, 'count': row.count} for row in rows]}


@router.get('/stats/ai', summary='AI效果与数据覆盖概览')
def get_ai_stats(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    total_items = db.query(Item).filter(Item.is_deleted.is_(False), Item.owner_deleted.is_(False)).count()
    image_items = db.query(Item).filter(Item.is_deleted.is_(False), Item.owner_deleted.is_(False), Item.image_url.isnot(None)).count()
    categorized_items = db.query(Item).filter(Item.is_deleted.is_(False), Item.owner_deleted.is_(False), Item.category.isnot(None)).count()
    feature_items = db.query(Item).filter(Item.is_deleted.is_(False), Item.owner_deleted.is_(False), Item.feature_text.isnot(None)).count()
    keyword_items = db.query(Item).filter(Item.is_deleted.is_(False), Item.owner_deleted.is_(False), Item.keywords.isnot(None)).count()
    vector_items = db.query(Item).filter(Item.is_deleted.is_(False), Item.owner_deleted.is_(False), Item.feature_vector.isnot(None)).count()
    location_items = db.query(Item).filter(Item.is_deleted.is_(False), Item.owner_deleted.is_(False), Item.location.isnot(None)).count()
    brand_items = db.query(Item).filter(Item.is_deleted.is_(False), Item.owner_deleted.is_(False), Item.brand.isnot(None)).count()
    color_items = db.query(Item).filter(Item.is_deleted.is_(False), Item.owner_deleted.is_(False), Item.color.isnot(None)).count()

    quality_sum = db.query(
        func.sum(
            case((Item.category.isnot(None), 1), else_=0)
            + case((Item.feature_text.isnot(None), 1), else_=0)
            + case((Item.location.isnot(None), 1), else_=0)
            + case((Item.brand.isnot(None), 1), else_=0)
            + case((Item.color.isnot(None), 1), else_=0)
        )
    ).filter(Item.is_deleted.is_(False), Item.owner_deleted.is_(False)).scalar() or 0

    avg_quality = round((quality_sum / (max(total_items, 1) * 5)) * 100, 1)

    total_matches = db.query(Match).count()
    confirmed_matches = db.query(Match).filter(Match.status.in_(['confirmed', 'completed'])).count()
    completed_matches = db.query(Match).filter(Match.status == 'completed').count()
    rejected_matches = db.query(Match).filter(Match.status == 'rejected').count()

    match_confirmation_rate = round((confirmed_matches / max(total_matches, 1)) * 100, 1) if total_matches else 0
    claim_completion_rate = round((completed_matches / max(confirmed_matches, 1)) * 100, 1) if confirmed_matches else 0
    ai_closed_loop_rate = round((completed_matches / max(total_matches, 1)) * 100, 1) if total_matches else 0
    rejection_rate = round((rejected_matches / max(total_matches, 1)) * 100, 1) if total_matches else 0

    category_rows = (
        db.query(Item.category, func.count(Item.id).label('count'))
        .filter(Item.is_deleted.is_(False), Item.owner_deleted.is_(False), Item.category.isnot(None))
        .group_by(Item.category)
        .order_by(func.count(Item.id).desc())
        .limit(6)
        .all()
    )

    return {
        'overview': {
            'total_items': total_items,
            'image_items': image_items,
            'avg_quality': avg_quality,
            'vector_items': vector_items,
            'total_matches': total_matches,
            'confirmed_matches': confirmed_matches,
            'completed_matches': completed_matches,
            'categorized_items': categorized_items,
            'feature_items': feature_items,
            'keyword_items': keyword_items,
        },
        'effect_metrics': {
            'match_confirmation_rate': match_confirmation_rate,
            'claim_completion_rate': claim_completion_rate,
            'ai_closed_loop_rate': ai_closed_loop_rate,
            'rejection_rate': rejection_rate,
            'classification_coverage_rate': round((categorized_items / max(image_items, 1)) * 100, 1) if image_items else 0,
            'feature_completion_rate': round((feature_items / max(total_items, 1)) * 100, 1) if total_items else 0,
            'keyword_completion_rate': round((keyword_items / max(total_items, 1)) * 100, 1) if total_items else 0,
        },
        'business_metrics': [
            {
                'name': '匹配确认率',
                'value': match_confirmation_rate,
                'numerator': confirmed_matches,
                'denominator': total_matches,
                'description': '所有匹配申请中，最终进入已确认或已完成状态的比例',
            },
            {
                'name': '认领完成率',
                'value': claim_completion_rate,
                'numerator': completed_matches,
                'denominator': confirmed_matches,
                'description': '已确认匹配中，最终完成线下交接并闭环的比例',
            },
            {
                'name': 'AI闭环成功率',
                'value': ai_closed_loop_rate,
                'numerator': completed_matches,
                'denominator': total_matches,
                'description': '从匹配申请到最终完成认领的整体闭环比例',
            },
            {
                'name': '误匹配拦截率',
                'value': rejection_rate,
                'numerator': rejected_matches,
                'denominator': total_matches,
                'description': '被人工拒绝的匹配占比，可反映系统误匹配被识别与拦截的情况',
            },
        ],
        'modules': [
            {
                'name': '图像分类',
                'coverage': round((categorized_items / max(image_items, 1)) * 100, 1) if image_items else 0,
                'count': categorized_items,
                'base': image_items,
                'description': '已上传图片中成功生成分类结果的比例',
            },
            {
                'name': '特征词提取',
                'coverage': round((feature_items / max(total_items, 1)) * 100, 1) if total_items else 0,
                'count': feature_items,
                'base': total_items,
                'description': '记录中成功提取典型特征摘要的比例',
            },
            {
                'name': '以图搜图',
                'coverage': round((vector_items / max(image_items, 1)) * 100, 1) if image_items else 0,
                'count': vector_items,
                'base': image_items,
                'description': '已生成视觉特征向量、可参与相似检索的图片比例',
            },
            {
                'name': 'LLM增强',
                'coverage': round((keyword_items / max(total_items, 1)) * 100, 1) if total_items else 0,
                'count': keyword_items,
                'base': total_items,
                'description': '记录中成功生成关键词与语义特征的比例',
            },
        ],
        'data_quality': [
            {'label': '类别字段', 'value': categorized_items, 'coverage': round((categorized_items / max(total_items, 1)) * 100, 1) if total_items else 0},
            {'label': '品牌字段', 'value': brand_items, 'coverage': round((brand_items / max(total_items, 1)) * 100, 1) if total_items else 0},
            {'label': '颜色字段', 'value': color_items, 'coverage': round((color_items / max(total_items, 1)) * 100, 1) if total_items else 0},
            {'label': '地点字段', 'value': location_items, 'coverage': round((location_items / max(total_items, 1)) * 100, 1) if total_items else 0},
            {'label': '关键词字段', 'value': keyword_items, 'coverage': round((keyword_items / max(total_items, 1)) * 100, 1) if total_items else 0},
            {'label': '典型特征', 'value': feature_items, 'coverage': round((feature_items / max(total_items, 1)) * 100, 1) if total_items else 0},
        ],
        'category_distribution': [{'name': row.category, 'value': row.count} for row in category_rows],
    }
