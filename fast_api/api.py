from fastapi import APIRouter
from fast_api.routes import (
    auth,
    recycled_sims,
    nin_linkages,
    bvn_linkages,
    delink_requests,
    notifications,
    audit_logs,
    dashboard,
    webhooks,
    retention,
    data_subject,
    identity,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(recycled_sims.router)
api_router.include_router(nin_linkages.router)
api_router.include_router(bvn_linkages.router)
api_router.include_router(delink_requests.router)
api_router.include_router(notifications.router)
api_router.include_router(audit_logs.router)
api_router.include_router(dashboard.router)
api_router.include_router(webhooks.router)
api_router.include_router(retention.router)
api_router.include_router(data_subject.router)
api_router.include_router(identity.router)
