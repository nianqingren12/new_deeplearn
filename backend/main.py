from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.auth import decode_token, get_current_token, hash_password, issue_token, security, verify_password
from backend.db import (
    consume_report_credit,
    create_order,
    create_report,
    create_user,
    get_admin_overview,
    get_dashboard_overview,
    get_recognition_by_id,
    get_recent_recognitions,
    get_recent_orders,
    get_recent_reports,
    get_report_by_id,
    get_user_by_email,
    get_user_by_id,
    init_db,
    list_custom_training_requests,
    redeem_recharge_code,
    save_custom_training_request,
    save_recognition,
    update_custom_training_request_status,
    log_audit_action,
    save_user_calibration,
    get_user_calibration,
)
from backend.inference import (
    build_ad_recommendation,
    build_companion_reply,
    build_emotion_report,
    build_sequence_summary,
    build_workplace_assessment,
    predict_micro_expression,
    predict_micro_expression_sequence,
    get_inference_engine,
)


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class AuthPayload(BaseModel):
    email: str = Field(pattern=EMAIL_PATTERN)
    password: str = Field(min_length=6, max_length=128)


class ForgotPasswordPayload(BaseModel):
    email: str = Field(pattern=EMAIL_PATTERN)


class RecognitionPayload(BaseModel):
    image_data_url: str = Field(min_length=20)
    source_type: str = "camera"


class SequenceRecognitionPayload(BaseModel):
    frames: list[str] = Field(min_length=2, max_length=12)
    source_type: str = "upload-video"


class WorkplacePayload(BaseModel):
    scenario: str = Field(min_length=2, max_length=50)


class CompanionPayload(BaseModel):
    emotion: str = Field(min_length=1, max_length=20)


class PurchasePayload(BaseModel):
    plan_name: str


class RechargePayload(BaseModel):
    code: str = Field(min_length=5, max_length=50)


class CustomTrainingPayload(BaseModel):
    industry: str = Field(min_length=2, max_length=30)
    description: str = Field(min_length=10, max_length=500)


class LeadStatusPayload(BaseModel):
    status: str = Field(min_length=2, max_length=20)


app = FastAPI(
    title="微表情识别商业化原型",
    description="集用户注册、实时识别、报告生成、会员订阅和商业化功能于一体的可运行原型。",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/assets", StaticFiles(directory=FRONTEND_DIR), name="assets")


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> dict[str, Any]:
    token = get_current_token(credentials)
    payload = decode_token(token)
    user = get_user_by_id(payload["user_id"])
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    return user


def ensure_admin_access(current_user: dict[str, Any]) -> None:
    if current_user["membership_tier"] == "enterprise" or current_user["email"].startswith("admin@"):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="当前账号无企业管理权限")


@app.on_event("startup")
def startup_event() -> None:
    init_db()


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.post("/api/auth/register")
def register(payload: AuthPayload) -> dict[str, Any]:
    existing_user = get_user_by_email(payload.email.lower())
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该邮箱已注册")
    user = create_user(payload.email.lower(), hash_password(payload.password))
    return {
        "token": issue_token(user["id"], user["email"]),
        "user": {
            "id": user["id"],
            "email": user["email"],
            "membership_tier": user["membership_tier"],
            "report_credits": user["report_credits"],
        },
    }


@app.post("/api/auth/login")
def login(payload: AuthPayload) -> dict[str, Any]:
    user = get_user_by_email(payload.email.lower())
    if user is None or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误")
    return {
        "token": issue_token(user["id"], user["email"]),
        "user": {
            "id": user["id"],
            "email": user["email"],
            "membership_tier": user["membership_tier"],
            "report_credits": user["report_credits"],
        },
    }


@app.post("/api/auth/forgot-password")
def forgot_password(payload: ForgotPasswordPayload) -> dict[str, str]:
    return {"message": f"演示环境已为 {payload.email} 生成重置申请，请在正式环境接入邮件服务。"}


@app.get("/api/auth/me")
def me(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    overview = get_dashboard_overview(current_user["id"])
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "can_manage_leads": current_user["membership_tier"] == "enterprise" or current_user["email"].startswith("admin@"),
        **overview,
    }


@app.get("/api/dashboard/overview")
def dashboard_overview(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    return {
        **get_dashboard_overview(current_user["id"]),
        "recent_recognitions": get_recent_recognitions(current_user["id"]),
        "recent_reports": get_recent_reports(current_user["id"]),
        "recent_orders": get_recent_orders(current_user["id"]),
    }


@app.post("/api/recognition/realtime")
def realtime_recognition(
    payload: RecognitionPayload,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    result = predict_micro_expression(payload.image_data_url)
    record = save_recognition(current_user["id"], payload.source_type, result)
    return {
        "record": record,
        "message": "识别成功，已写入个人历史记录。",
    }


@app.post("/api/recognition/sequence")
def sequence_recognition(
    payload: SequenceRecognitionPayload,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    result = predict_micro_expression_sequence(payload.frames, payload.source_type)
    saved_records = []
    for frame in result["frames"]:
        saved_records.append(
            save_recognition(
                current_user["id"],
                payload.source_type,
                {
                    "label": frame["label"],
                    "confidence": frame["confidence"],
                    "intensity": frame["intensity"],
                    "duration_ms": frame["duration_ms"],
                    "secondary_label": frame["secondary_label"],
                    "engine": frame["engine"],
                    "engine_version": frame["engine_version"],
                    "note": f"序列分析第 {frame['frame_index']} 帧",
                },
            )
        )
    return {
        "summary": build_sequence_summary(result),
        "sequence": result,
        "saved_count": len(saved_records),
    }


@app.post("/api/reports/generate")
def generate_report(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    if not consume_report_credit(current_user["id"]):
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="免费报告次数已用完，请升级会员")
    recognitions = get_recent_recognitions(current_user["id"], limit=20)
    if len(recognitions) < 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="至少完成 3 次识别后再生成深度报告")
    report_details = build_emotion_report(recognitions)
    report = create_report(
        current_user["id"],
        report_type="emotion-insight",
        title="情绪深度分析报告",
        summary=report_details["summary"],
        details=report_details,
        paid=True,
    )
    return {
        "report": report,
        "message": "报告生成完成。",
    }


@app.get("/api/reports/{report_id}")
def report_detail(report_id: int, current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    report = get_report_by_id(current_user["id"], report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="报告不存在")
    return report


@app.get("/api/recognitions/{recognition_id}")
def recognition_detail(recognition_id: int, current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    recognition = get_recognition_by_id(current_user["id"], recognition_id)
    if recognition is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="识别记录不存在")
    return recognition


@app.post("/api/evaluations/workplace")
def workplace_assessment(
    payload: WorkplacePayload,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    recognitions = get_recent_recognitions(current_user["id"], limit=12)
    return build_workplace_assessment(recognitions, payload.scenario)


@app.post("/api/companion/respond")
def companion_reply(
    payload: CompanionPayload,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    return {
        "message": build_companion_reply(payload.emotion),
        "user_id": current_user["id"],
    }


@app.get("/api/system/health")
def system_health() -> dict[str, Any]:
    engine = get_inference_engine()
    return {
        "status": "operational",
        "engine": engine.name,
        "version": engine.version,
        "model_loaded": engine.name != "DemoEngine",
        "db_type": DB_TYPE,
        "server_time": utc_now()
    }


@app.post("/api/health/calibrate")
def calibrate(payload: dict[str, Any], current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    save_user_calibration(current_user["id"], payload)
    log_audit_action(current_user["id"], "calibration", "health-profile", "success")
    return {"message": "基准校准已保存，AI 评估严谨度已提升。"}


@app.post("/api/health/assessment")
def health_assessment(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    recognitions = get_recent_recognitions(current_user["id"], limit=20)
    calibration = get_user_calibration(current_user["id"])
    engine = get_inference_engine()
    log_audit_action(current_user["id"], "generate", "health-assessment", "success")
    return engine.build_health_assessment(recognitions, calibration)


@app.get("/api/data/export")
def export_data(current_user: dict[str, Any] = Depends(get_current_user)) -> PlainTextResponse:
    recognitions = get_recent_recognitions(current_user["id"], limit=100)
    # 添加 UTF-8 BOM 以解决 Excel 乱码问题
    lines = ["\ufeff时间,微表情,置信度,强度,持续时长(ms),引擎"]
    for item in recognitions:
        lines.append(
            f"{item['created_at']},{item['label']},{item['confidence']},{item['intensity']},{item['duration_ms']},{item['engine']}"
        )
    csv_content = "\n".join(lines)
    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="micro-expression-export.csv"'},
    )


@app.get("/api/membership/plans")
def membership_plans() -> list[dict[str, Any]]:
    return [
        {"name": "普通会员", "price": "9.9元/月", "amount": 9.9, "rights": ["每月 10 次报告", "基础陪伴互动", "识别历史存储"]},
        {"name": "高级会员", "price": "29.9元/月", "amount": 29.9, "rights": ["无限报告", "职场测评", "高级数据导出", "定制服务折扣"]},
        {"name": "企业会员", "price": "999元/年", "amount": 999.0, "rights": ["企业导出权限", "批量账号管理", "定制模型评估", "专属支持"]},
    ]


@app.post("/api/membership/purchase")
def purchase_membership(
    payload: PurchasePayload,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    plan_mapping = {
        "普通会员": ("普通会员", 9.9, 30),
        "basic": ("普通会员", 9.9, 30),
        "高级会员": ("高级会员", 29.9, 30),
        "pro": ("高级会员", 29.9, 30),
        "企业会员": ("企业会员", 999.0, 365),
        "enterprise": ("企业会员", 999.0, 365),
    }
    if payload.plan_name not in plan_mapping:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="会员类型不存在")
    product_type, amount, valid_days = plan_mapping[payload.plan_name]
    order = create_order(current_user["id"], product_type, amount, valid_days=valid_days)
    return {
        "order": order,
        "message": f"{product_type}开通成功。",
    }


@app.post("/api/membership/recharge")
def recharge_membership(
    payload: RechargePayload,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    result = redeem_recharge_code(current_user["id"], payload.code)
    if not result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="激活码无效或已被使用")
    return {
        "message": f"成功激活{result['tier']}，增加 {result['added_credits']} 次报告额度，有效期至 {result['expires_at']}",
        "result": result
    }


@app.get("/api/orders/history")
def orders_history(current_user: dict[str, Any] = Depends(get_current_user)) -> list[dict[str, Any]]:
    return get_recent_orders(current_user["id"])


@app.get("/api/courses")
def courses() -> list[dict[str, str]]:
    return [
        {"title": "微表情商业解读课", "type": "课程", "price": "59元", "description": "面向求职者、销售与管理者的高频场景解读训练。"},
        {"title": "情绪管理咨询", "type": "1对1咨询", "price": "199元", "description": "结合识别报告给出个性化表达优化建议。"},
        {"title": "企业沟通工作坊", "type": "企业服务", "price": "定制报价", "description": "面向 HR 与管理团队的团体培训方案。"},
    ]


@app.post("/api/custom-training/request")
def request_custom_training(
    payload: CustomTrainingPayload,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    request_record = save_custom_training_request(current_user["id"], payload.industry, payload.description)
    return {
        "request": request_record,
        "message": "定制训练需求已提交，商务顾问将跟进评估。",
    }


@app.get("/api/ads/recommendation")
def ads_recommendation(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    overview = get_dashboard_overview(current_user["id"])
    return build_ad_recommendation(overview["dominant_emotion"])


@app.patch("/api/admin/leads/{lead_id}")
def update_lead_status(
    lead_id: int,
    payload: LeadStatusPayload,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    ensure_admin_access(current_user)
    update_custom_training_request_status(lead_id, payload.status)
    log_audit_action(current_user["id"], "update", f"lead:{lead_id}", "success")
    return {"message": "状态已更新"}


@app.get("/api/admin/audit-logs")
def get_audit_logs(current_user: dict[str, Any] = Depends(get_current_user)) -> list[dict[str, Any]]:
    ensure_admin_access(current_user)
    sql = "SELECT * FROM audit_logs ORDER BY id DESC LIMIT 50"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


@app.get("/api/admin/overview")
def admin_overview(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    ensure_admin_access(current_user)
    return get_admin_overview()


@app.get("/api/admin/leads")
def admin_leads(current_user: dict[str, Any] = Depends(get_current_user)) -> list[dict[str, Any]]:
    ensure_admin_access(current_user)
    return list_custom_training_requests()


@app.post("/api/admin/leads/{request_id}")
def admin_update_lead(
    request_id: int,
    payload: LeadStatusPayload,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    ensure_admin_access(current_user)
    updated = update_custom_training_request_status(request_id, payload.status)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="企业线索不存在")
    return updated
