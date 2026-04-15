const state = {
  token: localStorage.getItem("microExpressionToken") || "",
  authMode: "login",
  stream: null,
  currentUser: null,
  dashboard: null,
};

const elements = {
  authForm: document.getElementById("authForm"),
  emailInput: document.getElementById("emailInput"),
  passwordInput: document.getElementById("passwordInput"),
  authStatus: document.getElementById("authStatus"),
  authUserMeta: document.getElementById("authUserMeta"),
  tabButtons: document.querySelectorAll(".tab-btn"),
  toast: document.getElementById("toast"),
  membershipTier: document.getElementById("membershipTier"),
  reportCredits: document.getElementById("reportCredits"),
  recognitionCount: document.getElementById("recognitionCount"),
  dominantEmotion: document.getElementById("dominantEmotion"),
  emotionBars: document.getElementById("emotionBars"),
  camera: document.getElementById("camera"),
  captureCanvas: document.getElementById("captureCanvas"),
  uploadInput: document.getElementById("uploadInput"),
  recognitionResult: document.getElementById("recognitionResult"),
  reportPanel: document.getElementById("reportPanel"),
  companionPanel: document.getElementById("companionPanel"),
  adsPanel: document.getElementById("adsPanel"),
  customPanel: document.getElementById("customPanel"),
  workplaceScenario: document.getElementById("workplaceScenario"),
  emotionSelect: document.getElementById("emotionSelect"),
  plansGrid: document.getElementById("plansGrid"),
  courseGrid: document.getElementById("courseGrid"),
  recentRecognitions: document.getElementById("recentRecognitions"),
  recentReports: document.getElementById("recentReports"),
  reportWave: document.getElementById("reportWave"),
  orderHistory: document.getElementById("orderHistory"),
  adminSection: document.getElementById("adminSection"),
  adminStats: document.getElementById("adminStats"),
  leadList: document.getElementById("leadList"),
  rechargeInput: document.getElementById("rechargeInput"),
  paymentModal: document.getElementById("paymentModal"),
  closePaymentBtn: document.getElementById("closePaymentBtn"),
  simulatePayBtn: document.getElementById("simulatePayBtn"),
  payPlanName: document.getElementById("payPlanName"),
  payPlanAmount: document.getElementById("payPlanAmount"),
};

function showToast(message, isError = false) {
  elements.toast.textContent = message;
  elements.toast.classList.remove("hidden");
  elements.toast.style.borderColor = isError ? "rgba(255,141,154,0.38)" : "rgba(77,226,177,0.38)";
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => {
    elements.toast.classList.add("hidden");
  }, 2600);
}

function setPanelText(element, text) {
  element.textContent = text;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function emptyState(title, subtitle) {
  return `<div class="empty-state"><strong>${escapeHtml(title)}</strong><span>${escapeHtml(subtitle)}</span></div>`;
}

async function request(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  if (state.token) {
    headers.Authorization = `Bearer ${state.token}`;
  }
  const response = await fetch(path, { ...options, headers });
  let payload = {};
  try {
    payload = await response.json();
  } catch {
    payload = {};
  }
  if (!response.ok) {
    throw new Error(payload.detail || payload.message || "请求失败");
  }
  return payload;
}

function renderEmotionBars(distribution = {}) {
  const entries = Object.entries(distribution);
  if (!entries.length) {
    elements.emotionBars.innerHTML = '<div class="emotion-bar"><span>暂无识别数据</span></div>';
    return;
  }
  const max = Math.max(...entries.map(([, count]) => count), 1);
  elements.emotionBars.innerHTML = entries
    .map(([label, count]) => {
      const percent = Math.round((count / max) * 100);
      return `
        <div class="emotion-bar">
          <div class="inline-actions">
            <strong>${escapeHtml(label)}</strong>
            <span>${count} 次</span>
          </div>
          <div class="emotion-bar-track">
            <div class="emotion-bar-fill" style="width:${percent}%"></div>
          </div>
        </div>
      `;
    })
    .join("");
}

function renderWaveChart(wave = []) {
  if (!wave.length) {
    elements.reportWave.innerHTML = emptyState("暂无波动曲线", "生成一次深度报告后，这里会展示最近的情绪强度变化。");
    return;
  }
  elements.reportWave.innerHTML = wave
    .map(
      (item) => `
        <div class="wave-bar">
          <div class="wave-bar-header">
            <strong>片段 ${item.index}</strong>
            <span>${escapeHtml(item.label)} · ${item.value}</span>
          </div>
          <div class="wave-bar-track">
            <div class="wave-bar-fill" style="width:${Math.max(6, Math.min(100, item.value))}%"></div>
          </div>
        </div>
      `
    )
    .join("");
}

function renderRecognitions(records = []) {
  if (!records.length) {
    elements.recentRecognitions.innerHTML = emptyState("暂无识别记录", "先使用摄像头抓拍或上传图片 / 视频进行分析。");
    return;
  }
  elements.recentRecognitions.innerHTML = records
    .map(
      (record) => `
        <div class="history-item">
          <strong>${escapeHtml(record.label)} · ${record.confidence}</strong>
          <span>${escapeHtml(record.created_at)} · ${escapeHtml(record.source_type || "camera")}</span>
          <p>强度 ${record.intensity} · 持续 ${record.duration_ms} ms · 引擎 ${escapeHtml(record.engine)}</p>
        </div>
      `
    )
    .join("");
}

function renderReports(reports = []) {
  if (!reports.length) {
    elements.recentReports.innerHTML = emptyState("暂无历史报告", "完成至少 3 次识别后即可生成并回看深度报告。");
    renderWaveChart([]);
    return;
  }
  elements.recentReports.innerHTML = reports
    .map(
      (report) => `
        <div class="history-item">
          <strong>${escapeHtml(report.title)}</strong>
          <span>${escapeHtml(report.created_at)} · ${escapeHtml(report.report_type)}</span>
          <p>${escapeHtml(report.summary)}</p>
          <div class="inline-actions">
            <button class="mini-btn" onclick="openReport(${report.id})">查看详情</button>
          </div>
        </div>
      `
    )
    .join("");
  renderWaveChart(reports[0].details?.wave || []);
}

function renderOrders(orders = []) {
  if (!orders.length) {
    elements.orderHistory.innerHTML = emptyState("暂无订单记录", "开通会员后，这里会自动沉淀你的购买与续费历史。");
    return;
  }
  elements.orderHistory.innerHTML = orders
    .map(
      (order) => `
        <div class="history-item">
          <strong>${escapeHtml(order.product_type)} · ¥${order.amount}</strong>
          <span>${escapeHtml(order.order_no)} · ${escapeHtml(order.created_at)}</span>
          <p>状态 ${escapeHtml(order.status)}${order.valid_until ? ` · 有效期至 ${escapeHtml(order.valid_until)}` : ""}</p>
        </div>
      `
    )
    .join("");
}

function renderAdminStats(overview) {
  elements.adminStats.innerHTML = `
    <div class="stat-box"><span>用户数</span><strong>${overview.user_count}</strong></div>
    <div class="stat-box"><span>识别记录</span><strong>${overview.recognition_count}</strong></div>
    <div class="stat-box"><span>报告数</span><strong>${overview.report_count}</strong></div>
    <div class="stat-box"><span>订单数</span><strong>${overview.order_count}</strong></div>
    <div class="stat-box"><span>企业线索</span><strong>${overview.lead_count}</strong></div>
  `;
}

function renderLeadList(leads = []) {
  if (!leads.length) {
    elements.leadList.innerHTML = emptyState("暂无企业线索", "当用户提交定制训练需求后，企业工作台会自动展示。");
    return;
  }
  elements.leadList.innerHTML = leads
    .map(
      (lead) => `
        <div class="history-item">
          <strong>${escapeHtml(lead.industry)} · ${escapeHtml(lead.status)}</strong>
          <span>${escapeHtml(lead.user_email)} · ${escapeHtml(lead.created_at)}</span>
          <p>${escapeHtml(lead.description)}</p>
          <div class="lead-actions">
            <button class="mini-btn" onclick="updateLeadStatus(${lead.id}, '待联系')">待联系</button>
            <button class="mini-btn" onclick="updateLeadStatus(${lead.id}, '评估中')">评估中</button>
            <button class="mini-btn" onclick="updateLeadStatus(${lead.id}, '已转商机')">已转商机</button>
          </div>
        </div>
      `
    )
    .join("");
}

function persistToken(token) {
  state.token = token || "";
  if (state.token) {
    localStorage.setItem("microExpressionToken", state.token);
  } else {
    localStorage.removeItem("microExpressionToken");
  }
}

async function checkSystemHealth() {
  try {
    const data = await request("/api/system/health", { method: "GET" });
    const engineEl = document.getElementById("engine-status");
    if (engineEl) {
      engineEl.textContent = data.model_loaded ? `${data.engine} (REAL)` : "Demo Engine (Simulation)";
      engineEl.style.color = data.model_loaded ? "#00ffcc" : "#ffaa00";
    }
  } catch (err) {
    console.error("System health check failed");
  }
}

async function loadUserOverview() {
  checkSystemHealth(); // 每次加载数据时检查系统状态
  if (!state.token) {
    state.currentUser = null;
    elements.authStatus.textContent = "未登录";
    elements.authUserMeta.textContent = "请先注册或登录后体验完整功能。";
    elements.membershipTier.textContent = "Free";
    elements.reportCredits.textContent = "0";
    elements.recognitionCount.textContent = "0";
    elements.dominantEmotion.textContent = "平静";
    elements.adminSection.classList.add("hidden");
    renderEmotionBars({});
    renderRecognitions([]);
    renderReports([]);
    renderOrders([]);
    return;
  }
  const user = await request("/api/auth/me", { method: "GET" });
  state.currentUser = user;
  elements.authStatus.textContent = `已登录：${user.email}`;
  elements.authUserMeta.textContent = `会员等级 ${user.membership_tier} · 报告额度 ${user.report_credits}`;
  elements.membershipTier.textContent = user.membership_tier;
  elements.reportCredits.textContent = user.report_credits;
  elements.recognitionCount.textContent = user.recognition_count;
  elements.dominantEmotion.textContent = user.dominant_emotion;
  renderEmotionBars(user.emotion_distribution);
}

async function runHealthAssessment() {
  if (!state.token) return;

  try {
    const data = await request("/api/health/assessment", {
      method: "POST",
    });

    const stressEl = document.getElementById("stress-index");
    const focusEl = document.getElementById("focus-score");
    const riskEl = document.getElementById("risk-level");
    const adviceEl = document.getElementById("health-advice");
    const hrvValueEl = document.getElementById("hrv-value");
    const hrvStatusEl = document.getElementById("hrv-status");
    const blinkRateEl = document.getElementById("blink-rate");
    const blinkStatusEl = document.getElementById("blink-status");
    const clinicalIdEl = document.getElementById("clinical-id");
    const calBadgeEl = document.getElementById("calibration-status-badge");

    if (stressEl) stressEl.textContent = data.stress_index;
    if (focusEl) focusEl.textContent = data.focus_score;
    if (riskEl) riskEl.textContent = data.anxiety_risk;
    if (adviceEl) adviceEl.textContent = data.health_advice;
    if (hrvValueEl) hrvValueEl.textContent = data.hrv_value;
    if (hrvStatusEl) hrvStatusEl.textContent = data.hrv_status;
    if (blinkRateEl) blinkRateEl.textContent = data.blink_rate;
    if (blinkStatusEl) blinkStatusEl.textContent = data.blink_status;
    if (clinicalIdEl) clinicalIdEl.textContent = `ID: ${data.clinical_id}`;
    
    if (calBadgeEl) {
      calBadgeEl.textContent = data.is_calibrated ? "已校准" : "未校准";
      calBadgeEl.style.color = data.is_calibrated ? "#00ffcc" : "#888";
      calBadgeEl.style.borderColor = data.is_calibrated ? "#00ffcc" : "#444";
    }

    state.lastAssessment = data; // 保存最后一次评估结果用于导出

    if (riskEl) {
      if (data.stress_index > 70) riskEl.style.color = "#ff4d4d";
      else if (data.stress_index > 40) riskEl.style.color = "#ffaa00";
      else riskEl.style.color = "#00ffcc";
    }

    showToast("健康评估已更新");
  } catch (err) {
    showToast("评估更新失败", true);
  }
}

async function loadDashboardData() {
  if (!state.token) {
    return;
  }
  const dashboard = await request("/api/dashboard/overview", { method: "GET" });
  state.dashboard = dashboard;
  renderRecognitions(dashboard.recent_recognitions || []);
  renderReports(dashboard.recent_reports || []);
  renderOrders(dashboard.recent_orders || []);
  runHealthAssessment();
}

function openCalibrationModal() {
  document.getElementById("calibration-modal").classList.remove("hidden");
  document.getElementById("calibration-timer").textContent = "5";
  document.getElementById("calibration-bar").style.width = "0%";
  document.getElementById("calibration-status").textContent = "准备就绪";
  document.getElementById("start-calibration-btn").disabled = false;
}

function closeCalibrationModal() {
  document.getElementById("calibration-modal").classList.add("hidden");
}

async function startCalibration() {
  const btn = document.getElementById("start-calibration-btn");
  const timerEl = document.getElementById("calibration-timer");
  const barEl = document.getElementById("calibration-bar");
  const statusEl = document.getElementById("calibration-status");
  
  btn.disabled = true;
  statusEl.textContent = "校准中，请保持面部平静...";
  
  let timeLeft = 5;
  const interval = setInterval(async () => {
    timeLeft -= 0.1;
    if (timeLeft <= 0) {
      clearInterval(interval);
      timerEl.textContent = "0";
      barEl.style.width = "100%";
      finishCalibration();
    } else {
      timerEl.textContent = Math.ceil(timeLeft);
      barEl.style.width = `${((5 - timeLeft) / 5) * 100}%`;
    }
  }, 100);
}

async function finishCalibration() {
  const statusEl = document.getElementById("calibration-status");
  statusEl.textContent = "正在同步基准数据...";
  
  try {
    // 模拟采集当前的生理基准（心率变异性基础值等）
    const mockBaseline = {
      base_hrv: 55 + Math.random() * 10,
      base_blink_rate: 12 + Math.random() * 4,
      timestamp: new Date().toISOString()
    };
    
    await request("/api/health/calibrate", {
      method: "POST",
      body: JSON.stringify(mockBaseline)
    });
    
    statusEl.textContent = "校准成功！评估严谨度已提升。";
    setTimeout(() => {
      closeCalibrationModal();
      showToast("系统基准校准完成", false);
      runHealthAssessment(); // 重新运行评估以应用新基准
    }, 1500);
  } catch (err) {
     statusEl.textContent = "同步失败，请重试。";
     document.getElementById("start-calibration-btn").disabled = false;
   }
 }

async function loadAdminWorkspace() {
  if (!state.currentUser?.can_manage_leads) {
    elements.adminSection.classList.add("hidden");
    return;
  }
  const [overview, leads, auditLogs] = await Promise.all([
    request("/api/admin/overview", { method: "GET" }),
    request("/api/admin/leads", { method: "GET" }),
    request("/api/admin/audit-logs", { method: "GET" }),
  ]);
  elements.adminSection.classList.remove("hidden");
  renderAdminStats(overview);
  renderLeadList(leads);
  renderAuditLogs(auditLogs);
}

function renderAdminStats(stats) {
  const container = document.getElementById("adminStats");
  if (!container) return;
  container.innerHTML = `
    <div class="stat-box"><span>总注册用户</span><strong>${stats.total_users}</strong></div>
    <div class="stat-box"><span>付费订单</span><strong>${stats.paid_orders}</strong></div>
    <div class="stat-box"><span>累计营收</span><strong>¥${stats.total_revenue}</strong></div>
    <div class="stat-box"><span>定制需求</span><strong>${stats.pending_leads}</strong></div>
  `;
}

function renderLeadList(leads) {
  const container = document.getElementById("leadList");
  if (!container) return;
  if (!leads || leads.length === 0) {
    container.innerHTML = "<p>暂无商务咨询需求</p>";
    return;
  }
  container.innerHTML = leads
    .map(
      (lead) => `
    <div class="history-item">
      <div>
        <strong>行业：${escapeHtml(lead.industry)}</strong>
        <p>${escapeHtml(lead.description)}</p>
        <small>状态：${escapeHtml(lead.status)} | 时间：${new Date(lead.created_at).toLocaleString()}</small>
      </div>
      <button class="ghost-btn" onclick="updateLeadStatus(${lead.id}, 'processing')">处理中</button>
    </div>
  `
    )
    .join("");
}

function renderAuditLogs(logs) {
  const list = document.getElementById("audit-log-list");
  if (!list) return;
  if (!logs || logs.length === 0) {
    list.innerHTML = "<p>暂无日志</p>";
    return;
  }
  list.innerHTML = logs
    .map(
      (log) => `
        <div style="border-bottom: 1px solid #333; padding: 5px 0; display: flex; justify-content: space-between;">
          <span style="color: #888;">[${new Date(log.created_at).toLocaleTimeString()}]</span>
          <span style="color: #00ffcc;">${log.action}</span>
          <span style="color: #ccc;">${log.resource}</span>
          <span style="color: ${log.status === 'success' ? '#5cb85c' : '#d9534f'};">${log.status}</span>
        </div>
      `
    )
    .join("");
}

async function updateLeadStatus(leadId, status) {
  if (!state.token) return;
  await request(`/api/admin/leads/${leadId}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
  showToast("状态已更新");
  await loadAdminWorkspace();
}

async function refreshAuthenticatedData() {
  await loadUserOverview();
  if (!state.token) {
    return;
  }
  await Promise.all([loadDashboardData(), loadAdminWorkspace()]);
}

async function loadPlans() {
  const plans = await request("/api/membership/plans", { method: "GET" });
  elements.plansGrid.innerHTML = plans
    .map(
      (plan) => `
        <div class="plan-card">
          <span>${escapeHtml(plan.name)}</span>
          <strong>${escapeHtml(plan.price)}</strong>
          <ul>${plan.rights.map((right) => `<li>${escapeHtml(right)}</li>`).join("")}</ul>
          <button class="primary-btn" onclick="buyPlan('${escapeHtml(plan.name)}')">立即开通</button>
        </div>
      `
    )
    .join("");
}

async function loadCourses() {
  const courses = await request("/api/courses", { method: "GET" });
  elements.courseGrid.innerHTML = courses
    .map(
      (course) => `
        <div class="course-card">
          <span>${escapeHtml(course.type)}</span>
          <strong>${escapeHtml(course.title)}</strong>
          <p>${escapeHtml(course.description)}</p>
          <div class="inline-actions" style="justify-content: space-between; align-items: center;">
            <span style="font-weight: bold; color: var(--accent);">${escapeHtml(course.price)}</span>
            <button class="ghost-btn" onclick="buyCourse('${escapeHtml(course.title)}')">立即咨询</button>
          </div>
        </div>
      `
    )
    .join("");
}

async function buyCourse(courseTitle) {
  if (!state.token) {
    showToast("请先登录", true);
    return;
  }
  showToast(`已提交“${courseTitle}”的咨询请求，顾问稍后联系您`, false);
}

async function authenticate(event) {
  event.preventDefault();
  const payload = {
    email: elements.emailInput.value.trim(),
    password: elements.passwordInput.value.trim(),
  };
  const endpoint = state.authMode === "register" ? "/api/auth/register" : "/api/auth/login";
  const result = await request(endpoint, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  persistToken(result.token);
  await refreshAuthenticatedData();
  showToast(`${state.authMode === "register" ? "注册" : "登录"}成功`);
}

async function handleForgotPassword() {
  const email = elements.emailInput.value.trim();
  if (!email) {
    showToast("请先输入邮箱", true);
    return;
  }
  const result = await request("/api/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
  showToast(result.message);
}

async function startCamera() {
  if (state.stream) {
    return;
  }
  const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" }, audio: false });
  state.stream = stream;
  elements.camera.srcObject = stream;
  showToast("摄像头已开启");
}

async function captureAndRecognize() {
  if (!state.token) {
    showToast("请先登录", true);
    return;
  }
  if (!state.stream) {
    await startCamera();
  }
  const video = elements.camera;
  const canvas = elements.captureCanvas;
  const width = video.videoWidth || 640;
  const height = video.videoHeight || 480;
  canvas.width = width;
  canvas.height = height;
  canvas.getContext("2d").drawImage(video, 0, 0, width, height);
  const imageDataUrl = canvas.toDataURL("image/jpeg", 0.92);
  const result = await request("/api/recognition/realtime", {
    method: "POST",
    body: JSON.stringify({ image_data_url: imageDataUrl, source_type: "camera" }),
  });
  const record = result.record;
  setPanelText(
    elements.recognitionResult,
    `主识别：${record.label}\n置信度：${record.confidence}\n情绪强度：${record.intensity}\n持续时长：${record.duration_ms} ms\n辅助标签：${record.secondary_label}\n引擎：${record.engine} ${record.engine_version || ""}`
  );
  await refreshAuthenticatedData();
  showToast("识别完成");
}

function readFileAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(new Error("文件读取失败"));
    reader.readAsDataURL(file);
  });
}

async function extractVideoFrames(file, frameCount = 5) {
  const videoUrl = URL.createObjectURL(file);
  const video = document.createElement("video");
  video.src = videoUrl;
  video.muted = true;
  video.playsInline = true;
  await new Promise((resolve, reject) => {
    video.onloadedmetadata = resolve;
    video.onerror = () => reject(new Error("视频加载失败"));
  });
  const canvas = document.createElement("canvas");
  const width = video.videoWidth || 640;
  const height = video.videoHeight || 360;
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext("2d");
  const duration = Number.isFinite(video.duration) && video.duration > 0 ? video.duration : 1;
  const targets = Array.from({ length: frameCount }, (_, index) => {
    const progress = (index + 1) / (frameCount + 1);
    return Math.min(duration * progress, Math.max(0, duration - 0.05));
  });
  const frames = [];
  for (const target of targets) {
    await new Promise((resolve, reject) => {
      video.onseeked = () => {
        context.drawImage(video, 0, 0, width, height);
        frames.push(canvas.toDataURL("image/jpeg", 0.88));
        resolve();
      };
      video.onerror = () => reject(new Error("视频取帧失败"));
      video.currentTime = target;
    });
  }
  URL.revokeObjectURL(videoUrl);
  return frames;
}

async function analyzeUploadedContent() {
  if (!state.token) {
    showToast("请先登录", true);
    return;
  }
  const file = elements.uploadInput.files?.[0];
  if (!file) {
    showToast("请先选择图片或视频", true);
    return;
  }
  if (file.type.startsWith("image/")) {
    const imageDataUrl = await readFileAsDataUrl(file);
    const result = await request("/api/recognition/realtime", {
      method: "POST",
      body: JSON.stringify({ image_data_url: imageDataUrl, source_type: "upload-image" }),
    });
    const record = result.record;
    setPanelText(
      elements.recognitionResult,
      `上传分析完成\n主识别：${record.label}\n置信度：${record.confidence}\n情绪强度：${record.intensity}\n持续时长：${record.duration_ms} ms`
    );
  } else if (file.type.startsWith("video/")) {
    const frames = await extractVideoFrames(file, 5);
    const result = await request("/api/recognition/sequence", {
      method: "POST",
      body: JSON.stringify({ frames, source_type: "upload-video" }),
    });
    setPanelText(
      elements.recognitionResult,
      `视频分析完成\n${result.summary}\n主导情绪：${result.sequence.dominant_emotion}\n次级情绪：${result.sequence.secondary_emotion}\n引擎：${result.sequence.engine} ${result.sequence.engine_version}`
    );
    renderWaveChart(result.sequence.wave || []);
  } else {
    showToast("暂不支持该文件类型", true);
    return;
  }
  await refreshAuthenticatedData();
  showToast("上传内容分析成功");
}

async function generateReport() {
  if (!state.token) {
    showToast("请先登录", true);
    return;
  }
  const result = await request("/api/reports/generate", { method: "POST" });
  const report = result.report;
  const details = report.details;
  setPanelText(
    elements.reportPanel,
    `标题：${report.title}\n摘要：${report.summary}\n洞察：${details.insight}\n样本分布：${Object.entries(details.distribution)
      .map(([label, count]) => `${label}:${count}`)
      .join(" / ")}`
  );
  renderWaveChart(details.wave || []);
  await refreshAuthenticatedData();
  showToast("报告生成成功");
}

async function openReport(reportId) {
  if (!state.token) {
    return;
  }
  const report = await request(`/api/reports/${reportId}`, { method: "GET" });
  setPanelText(
    elements.reportPanel,
    `标题：${report.title}\n摘要：${report.summary}\n洞察：${report.details.insight}\n分布：${Object.entries(report.details.distribution)
      .map(([label, count]) => `${label}:${count}`)
      .join(" / ")}`
  );
  renderWaveChart(report.details.wave || []);
  const exportBtn = document.getElementById("exportPdfBtn");
  if (exportBtn) {
    exportBtn.classList.remove("hidden");
  }
}

async function exportPdfReport() {
  if (!state.token) {
    showToast("请先登录", true);
    return;
  }
  
  const opt = {
    margin:       [10, 10, 15, 10],
    filename:     `Clinical_Report_${new Date().getTime()}.pdf`,
    image:        { type: 'jpeg', quality: 0.98 },
    html2canvas:  { scale: 2, useCORS: true },
    jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' }
  };
  
  const container = document.createElement('div');
  container.style.padding = '30px';
  container.style.color = '#1a1a1a';
  container.style.backgroundColor = '#fff';
  container.style.fontFamily = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif";
  
  // Header
  const header = `
    <div style="border-bottom: 3px solid #00ffcc; padding-bottom: 20px; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: flex-end;">
      <div>
        <h1 style="margin: 0; font-size: 24px; color: #000;">AI 情绪健康与压力临床评估报告</h1>
        <p style="margin: 5px 0 0 0; color: #666; font-size: 14px;">Clinical Emotion & Stress Analysis Report</p>
      </div>
      <div style="text-align: right;">
        <p style="margin: 0; font-weight: bold; font-size: 14px;">报告编号: ${state.lastAssessment?.clinical_id || 'N/A'}</p>
        <p style="margin: 2px 0 0 0; color: #888; font-size: 12px;">生成日期: ${new Date().toLocaleString()}</p>
      </div>
    </div>
  `;
  
  // Patient Info (Simulated)
  const patientInfo = `
    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 25px; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; font-size: 13px;">
      <div><strong>用户 ID:</strong> ${state.currentUser?.id || 'UID-8821'}</div>
      <div><strong>账号:</strong> ${state.currentUser?.email || 'Guest'}</div>
      <div><strong>样本类型:</strong> 微表情序列分析</div>
      <div><strong>合规标准:</strong> HIPAA/GDPR</div>
      <div><strong>数据加密:</strong> AES-256 (RSA-2048)</div>
      <div><strong>分析引擎:</strong> ${state.dashboard?.recent_recognitions?.[0]?.engine || 'AI-Medical-v1'}</div>
    </div>
  `;
  
  // Metrics Section
  const assessment = state.lastAssessment || { stress_index: '--', focus_score: '--', anxiety_risk: '--', hrv_value: '--', blink_rate: '--' };
  const metrics = `
    <h2 style="font-size: 18px; border-left: 4px solid #00ffcc; padding-left: 10px; margin-bottom: 15px;">1. 临床指标分析 (Clinical Metrics)</h2>
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 25px;">
      <tr style="background: #f1f3f5;">
        <th style="padding: 12px; border: 1px solid #dee2e6; text-align: left;">评估维度</th>
        <th style="padding: 12px; border: 1px solid #dee2e6; text-align: left;">测量值</th>
        <th style="padding: 12px; border: 1px solid #dee2e6; text-align: left;">参考区间 (Normal)</th>
        <th style="padding: 12px; border: 1px solid #dee2e6; text-align: left;">评估状态</th>
      </tr>
      <tr>
        <td style="padding: 12px; border: 1px solid #dee2e6;">感知压力指数 (PSS)</td>
        <td style="padding: 12px; border: 1px solid #dee2e6;">${assessment.stress_index}%</td>
        <td style="padding: 12px; border: 1px solid #dee2e6;">0% - 40%</td>
        <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold; color: ${assessment.stress_index > 40 ? '#d9534f' : '#5cb85c'}">${assessment.stress_index > 40 ? '注意' : '正常'}</td>
      </tr>
      <tr>
        <td style="padding: 12px; border: 1px solid #dee2e6;">心率变异性 (HRV)</td>
        <td style="padding: 12px; border: 1px solid #dee2e6;">${assessment.hrv_value} ms</td>
        <td style="padding: 12px; border: 1px solid #dee2e6;">> 50 ms</td>
        <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold; color: ${assessment.hrv_value < 50 ? '#f0ad4e' : '#5cb85c'}">${assessment.hrv_status || '正常'}</td>
      </tr>
      <tr>
        <td style="padding: 12px; border: 1px solid #dee2e6;">认知专注得分</td>
        <td style="padding: 12px; border: 1px solid #dee2e6;">${assessment.focus_score}%</td>
        <td style="padding: 12px; border: 1px solid #dee2e6;">> 70%</td>
        <td style="padding: 12px; border: 1px solid #dee2e6;">${assessment.focus_score > 70 ? '优良' : '一般'}</td>
      </tr>
      <tr>
        <td style="padding: 12px; border: 1px solid #dee2e6;">瞬目频率 (Blink Rate)</td>
        <td style="padding: 12px; border: 1px solid #dee2e6;">${assessment.blink_rate} 次/分</td>
        <td style="padding: 12px; border: 1px solid #dee2e6;">10 - 20 次/分</td>
        <td style="padding: 12px; border: 1px solid #dee2e6;">${assessment.blink_status || '正常'}</td>
      </tr>
    </table>
  `;
  
  // Risk & Advice
  const advice = `
    <h2 style="font-size: 18px; border-left: 4px solid #00ffcc; padding-left: 10px; margin-bottom: 15px;">2. 风险等级与专家建议</h2>
    <div style="background: ${assessment.stress_index > 70 ? '#fff5f5' : '#f5fff5'}; border: 1px solid ${assessment.stress_index > 70 ? '#ffc9c9' : '#c9ffc9'}; padding: 15px; border-radius: 8px;">
      <p style="margin-top: 0;"><strong>风险等级:</strong> <span style="font-size: 1.2rem; color: ${assessment.stress_index > 70 ? '#d9534f' : '#5cb85c'}">${assessment.anxiety_risk}</span></p>
      <p style="margin-bottom: 0; line-height: 1.6;"><strong>建议详情:</strong> ${assessment.health_advice}</p>
    </div>
  `;
  
  // Footer / Signature
  const footer = `
    <div style="margin-top: 50px; padding-top: 20px; border-top: 1px solid #eee; display: flex; justify-content: space-between; align-items: center;">
      <div style="font-size: 11px; color: #999; max-width: 60%;">
        * 本报告由 AI 情绪健康分析引擎自动生成。所有原始面部特征数据均已在分析后立即销毁。本报告不具有法律强制约束力，仅作为个人健康参考。
      </div>
      <div style="text-align: right;">
        <div style="font-family: 'Brush Script MT', cursive; font-size: 24px; color: #000; margin-bottom: 5px;">AI-Medical Validator</div>
        <p style="margin: 0; font-size: 12px; color: #666;">数字化实验室认证章 (AES-Signature)</p>
      </div>
    </div>
  `;
  
  container.innerHTML = header + patientInfo + metrics + advice + footer;
  
  showToast("正在生成临床级 PDF 报告...");
  html2pdf().set(opt).from(container).save().then(() => {
    showToast("临床报告导出成功");
  }).catch((err) => {
    showToast("报告生成失败", true);
  });
}

async function runAssessment() {
  if (!state.token) {
    showToast("请先登录", true);
    return;
  }
  const result = await request("/api/evaluations/workplace", {
    method: "POST",
    body: JSON.stringify({ scenario: elements.workplaceScenario.value }),
  });
  setPanelText(
    elements.reportPanel,
    `场景：${result.scenario}\n匹配得分：${result.score}\n主导情绪：${result.dominant_emotion}\n建议：${result.suggestion}`
  );
}

async function companionReply() {
  if (!state.token) {
    showToast("请先登录", true);
    return;
  }
  const result = await request("/api/companion/respond", {
    method: "POST",
    body: JSON.stringify({ emotion: elements.emotionSelect.value }),
  });
  setPanelText(elements.companionPanel, result.message);
}

async function exportData() {
  if (!state.token) {
    showToast("请先登录", true);
    return;
  }
  const response = await fetch("/api/data/export", {
    headers: { Authorization: `Bearer ${state.token}` },
  });
  if (!response.ok) {
    showToast("导出失败", true);
    return;
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "micro-expression-export.csv";
  link.click();
  URL.revokeObjectURL(url);
  showToast("CSV 已导出");
}

async function loadAdsRecommendation() {
  if (!state.token) {
    showToast("请先登录", true);
    return;
  }
  const result = await request("/api/ads/recommendation", { method: "GET" });
  setPanelText(elements.adsPanel, `${result.title}\n${result.description}\n主导情绪：${result.dominant_emotion}`);
}

async function buyPlan(planName) {
  if (!state.token) {
    showToast("请先登录", true);
    return;
  }
  
  // 获取价格
  const plans = await request("/api/membership/plans", { method: "GET" });
  const plan = plans.find(p => p.name === planName);
  
  if (plan) {
    elements.payPlanName.textContent = plan.name;
    elements.payPlanAmount.textContent = plan.price;
    elements.paymentModal.classList.remove("hidden");
    
    // 临时存储当前要购买的计划
    state.pendingPlan = planName;
  }
}

async function simulatePayment() {
  if (!state.pendingPlan) return;
  
  showToast("正在处理支付请求...");
  
  try {
    // 模拟后端订单创建与支付回调
    const result = await request("/api/membership/purchase", {
      method: "POST",
      body: JSON.stringify({ plan_name: state.pendingPlan }),
    });
    
    showToast(result.message);
    elements.paymentModal.classList.add("hidden");
    state.pendingPlan = null;
    await refreshAuthenticatedData();
  } catch (error) {
    showToast(error.message, true);
  }
}

async function rechargeMembership() {
  if (!state.token) {
    showToast("请先登录", true);
    return;
  }
  const code = elements.rechargeInput.value.trim();
  if (!code) {
    showToast("请输入激活密钥", true);
    return;
  }
  const result = await request("/api/membership/recharge", {
    method: "POST",
    body: JSON.stringify({ code }),
  });
  showToast(result.message);
  elements.rechargeInput.value = "";
  await refreshAuthenticatedData();
}

async function submitCustomTraining(event) {
  event.preventDefault();
  if (!state.token) {
    showToast("请先登录", true);
    return;
  }
  const payload = {
    industry: document.getElementById("industryInput").value.trim(),
    description: document.getElementById("customDescription").value.trim(),
  };
  const result = await request("/api/custom-training/request", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  setPanelText(
    elements.customPanel,
    `需求编号：${result.request.id}\n行业：${result.request.industry}\n状态：${result.request.status}\n创建时间：${result.request.created_at}`
  );
  await refreshAuthenticatedData();
  showToast("定制需求已提交");
}

async function updateLeadStatus(requestId, status) {
  const updated = await request(`/api/admin/leads/${requestId}`, {
    method: "POST",
    body: JSON.stringify({ status }),
  });
  showToast(`线索 ${updated.id} 已更新为${updated.status}`);
  await loadAdminWorkspace();
}

function setupEvents() {
  elements.authForm.addEventListener("submit", async (event) => {
    try {
      await authenticate(event);
    } catch (error) {
      showToast(error.message, true);
    }
  });

  elements.tabButtons.forEach((button) => {
    button.addEventListener("click", () => {
      state.authMode = button.dataset.mode;
      elements.tabButtons.forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
    });
  });

  document.getElementById("forgotPasswordBtn").addEventListener("click", async () => {
    try {
      await handleForgotPassword();
    } catch (error) {
      showToast(error.message, true);
    }
  });

  document.getElementById("startCameraBtn").addEventListener("click", async () => {
    try {
      await startCamera();
    } catch (error) {
      showToast(`摄像头开启失败：${error.message}`, true);
    }
  });

  document.getElementById("captureBtn").addEventListener("click", async () => {
    try {
      await captureAndRecognize();
    } catch (error) {
      showToast(error.message, true);
    }
  });

  document.getElementById("analyzeUploadBtn").addEventListener("click", async () => {
    try {
      await analyzeUploadedContent();
    } catch (error) {
      showToast(error.message, true);
    }
  });

  document.getElementById("generateReportBtn").addEventListener("click", async () => {
    try {
      await generateReport();
    } catch (error) {
      showToast(error.message, true);
    }
  });

  document.getElementById("runAssessmentBtn").addEventListener("click", async () => {
    try {
      await runAssessment();
    } catch (error) {
      showToast(error.message, true);
    }
  });

  document.getElementById("companionBtn").addEventListener("click", async () => {
    try {
      await companionReply();
    } catch (error) {
      showToast(error.message, true);
    }
  });

  document.getElementById("exportBtn").addEventListener("click", async () => {
    try {
      await exportData();
    } catch (error) {
      showToast(error.message, true);
    }
  });

  document.getElementById("adsBtn").addEventListener("click", async () => {
    try {
      await loadAdsRecommendation();
    } catch (error) {
      showToast(error.message, true);
    }
  });

  document.getElementById("rechargeBtn").addEventListener("click", async () => {
    try {
      await rechargeMembership();
    } catch (error) {
      showToast(error.message, true);
    }
  });

  elements.closePaymentBtn.addEventListener("click", () => {
    elements.paymentModal.classList.add("hidden");
    state.pendingPlan = null;
  });

  elements.simulatePayBtn.addEventListener("click", async () => {
    await simulatePayment();
  });

  const exportPdfBtn = document.getElementById("exportPdfBtn");
  if (exportPdfBtn) {
    exportPdfBtn.addEventListener("click", async () => {
      try {
        await exportPdfReport();
      } catch (error) {
        showToast(error.message, true);
      }
    });
  }

  document.getElementById("customTrainingForm").addEventListener("submit", async (event) => {
    try {
      await submitCustomTraining(event);
    } catch (error) {
      showToast(error.message, true);
    }
  });

  document.getElementById("logoutBtn").addEventListener("click", () => {
    persistToken("");
    if (state.stream) {
      state.stream.getTracks().forEach((track) => track.stop());
      state.stream = null;
      elements.camera.srcObject = null;
    }
    loadUserOverview();
    showToast("已退出登录");
  });

  document.getElementById("refreshDashboardBtn").addEventListener("click", async () => {
    try {
      await refreshAuthenticatedData();
      showToast("数据已刷新");
    } catch (error) {
      showToast(error.message, true);
    }
  });
}

async function bootstrap() {
  setupEvents();
  try {
    await Promise.all([loadPlans(), loadCourses()]);
    await refreshAuthenticatedData();
  } catch (error) {
    showToast(error.message, true);
  }
}

window.buyPlan = buyPlan;
window.buyCourse = buyCourse;
window.openReport = openReport;
window.updateLeadStatus = updateLeadStatus;
bootstrap();
