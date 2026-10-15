"""漏洞知识库 / 提交规范指引 / 合规风险提示（内置知识内容，只读接口）。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_current_user
from app.models import User

router = APIRouter(prefix="/kb", tags=["knowledge"])

# 漏洞知识库：常见众测高价值漏洞类型的识别、危害与修复要点
_ARTICLES: list[dict] = [
    {
        "id": "kb-sqli",
        "category": "注入类",
        "title": "SQL 注入",
        "cwe": "CWE-89",
        "severity": "critical",
        "summary": "用户可控输入拼接进 SQL 语句，导致数据泄露、篡改或数据库被接管。",
        "detail": "## 识别\n- 参数直接拼接 SQL 字符串，未使用预编译/参数化查询。\n"
                  "- 报错信息回显数据库类型与语句片段。\n\n## 危害\n- 拖库（读取任意表）、越权读写、' OR '1'='1 绕过认证。\n\n"
                  "## 验证要点\n- 优先使用 `sqlmap` 或手工布尔/时间盲注验证；只读取必要数据，禁止写库或删表。\n\n"
                  "## 修复\n- 全部使用参数化查询/ORM 绑定；最小权限数据库账号；输入白名单校验。",
    },
    {
        "id": "kb-xss",
        "category": "注入类",
        "title": "跨站脚本（XSS）",
        "cwe": "CWE-79",
        "severity": "high",
        "summary": "不可信输入未经过滤/转义输出到 HTML/JS，导致脚本在受害者浏览器执行。",
        "detail": "## 识别\n- 反射型：搜索/跳转参数回显；存储型：评论、昵称、工单内容；DOM 型：`innerHTML`/`eval`。\n\n"
                  "## 危害\n- 窃取 Cookie/Token、会话劫持、前端钓鱼、蠕虫传播。\n\n"
                  "## 验证要点\n- 使用 `alert(1)`/`document.domain` 等无害 PoC，禁止收集真实用户凭据。\n\n"
                  "## 修复\n- 输出上下文编码、CSP 策略、富文本白名单过滤、HttpOnly Cookie。",
    },
    {
        "id": "kb-cmdi",
        "category": "注入类",
        "title": "命令注入 / 代码执行",
        "cwe": "CWE-78",
        "severity": "critical",
        "summary": "用户输入进入系统命令或动态执行函数，可执行任意命令获取服务器权限。",
        "detail": "## 识别\n- 调用 `system/exec/popen`，或语言层 `eval/assert/反序列化` 入口。\n\n"
                  "## 危害\n- 直接获取服务器 shell，横向渗透内网。\n\n"
                  "## 验证要点\n- 仅执行 `id`/`whoami` 等只读命令证明危害，严禁反弹 shell、植入后门。\n\n"
                  "## 修复\n- 避免拼接 shell 命令，使用参数数组而非字符串；白名单校验；沙箱执行。",
    },
    {
        "id": "kb-ssrf",
        "category": "服务端请求",
        "title": "SSRF 服务端请求伪造",
        "cwe": "CWE-918",
        "severity": "high",
        "summary": "服务端可被诱导发起任意请求，探测内网、读取云元数据或攻击内网服务。",
        "detail": "## 识别\n- URL/图片地址/回调地址类参数由用户控制；支持 `file://`、`dict://`、`gopher://` 等协议。\n\n"
                  "## 危害\n- 读取云厂商元数据（如 169.254.169.254）获取临时凭据；内网端口扫描与横向。\n\n"
                  "## 验证要点\n- 使用 DNSLog 或自有公网地址验证外连，禁止对内网目标做破坏性探测。\n\n"
                  "## 修复\n- 出站 URL 白名单、禁止内网网段、禁用危险协议、DNS 解析后二次校验（防 302 绕过）。",
    },
    {
        "id": "kb-idor",
        "category": "访问控制",
        "title": "越权访问（IDOR）",
        "cwe": "CWE-639",
        "severity": "high",
        "summary": "直接以对象标识访问资源而缺少归属校验，可横向/纵向读取或修改他人数据。",
        "detail": "## 识别\n- 请求中直接出现 `id/uid/orderId` 等对象标识，替换后可访问他人资源。\n\n"
                  "## 危害\n- 大规模用户数据泄露、越权操作（改密、下单、提现）。\n\n"
                  "## 验证要点\n- 使用两个自有测试账号交叉验证，禁止访问真实用户数据。\n\n"
                  "## 修复\n- 服务端强制归属校验（当前用户 vs 资源所有者）、不可预测 ID、统一鉴权中间件。",
    },
    {
        "id": "kb-upload",
        "category": "文件处理",
        "title": "文件上传与路径穿越",
        "cwe": "CWE-434",
        "severity": "critical",
        "summary": "上传校验不足导致上传可执行脚本，或通过 `../` 覆盖任意路径文件。",
        "detail": "## 识别\n- 仅前端校验后缀、黑名单过滤、Content-Type 可伪造；文件名拼接路径。\n\n"
                  "## 危害\n- 上传 Webshell 获取权限；覆盖配置/密钥文件。\n\n"
                  "## 验证要点\n- 仅上传无害的 txt/图片证明绕过，严禁上传真实 Webshell。\n\n"
                  "## 修复\n- 白名单扩展名、重命名存储、存储与执行分离（对象存储）、`os.path` 规范化校验。",
    },
    {
        "id": "kb-logic",
        "category": "业务逻辑",
        "title": "业务逻辑漏洞",
        "cwe": "CWE-840",
        "severity": "high",
        "summary": "因流程校验缺失产生的越权、并发、支付篡改、验证码与风控绕过等问题。",
        "detail": "## 常见类型\n- 验证码可复用/可暴力；短信/邮箱轰炸；\n"
                  "- 支付金额/数量篡改、优惠券叠加；\n- 并发领取、库存超卖；\n- 密码重置逻辑缺陷。\n\n"
                  "## 验证要点\n- 只做最小化、可复现的证明，禁止真实资金交易与批量轰炸。\n\n"
                  "## 修复\n- 服务端全链路校验、幂等与事务、频率限制、关键参数服务端计算。",
    },
    {
        "id": "kb-info",
        "category": "信息泄露",
        "title": "敏感信息泄露",
        "cwe": "CWE-200",
        "severity": "medium",
        "summary": "接口或前端资源泄露密钥、源码、内部地址、用户隐私等敏感数据。",
        "detail": "## 识别\n- 前端 JS/Map 文件含密钥；接口返回多余字段；调试接口/`.git`/备份文件暴露。\n\n"
                  "## 危害\n- 直接提供后续攻击入口，或造成用户隐私合规风险。\n\n"
                  "## 验证要点\n- 仅截图最小证据，避免下载/扩散大量数据。\n\n"
                  "## 修复\n- 密钥移出前端、响应字段裁剪、关闭调试与目录列举、加访问控制。",
    },
]

# 提交规范指引
_GUIDELINES: dict = {
    "title": "SRC 漏洞提交规范指引",
    "sections": [
        {"heading": "1. 提交前自检清单",
         "body": "- 确认目标在授权范围内（域名、IP、App、小程序、账号白名单）。\n"
                 "- 漏洞可稳定复现，且为最新版本。\n"
                 "- 已有他人提交的记录不重复提交（先搜索历史）。\n"
                 "- 危害证明最小化：不破坏数据、不获取真实用户隐私、不植入后门。\n"
                 "- 保留完整证据：请求/响应、时间、复现步骤。",
         },
        {"heading": "2. 报告结构（建议）",
         "body": "- **标题**：影响对象 + 漏洞类型 + 一句话影响。\n"
                 "- **基本信息**：URL/接口、参数、账号、版本、环境。\n"
                 "- **漏洞类型与等级**：CWE/OWASP 分类、CVSS 或平台等级。\n"
                 "- **复现步骤**：编号步骤 + 可复制的请求（脱敏）。\n"
                 "- **危害说明**：可造成的实际影响与影响面。\n"
                 "- **修复建议**：可落地的整改方案。\n"
                 "- **证据附件**：截图/抓包文件（关键信息打码）。",
         },
        {"heading": "3. 常见驳回原因",
         "body": "- 超出授权范围或使用未授权测试账号。\n"
                 "- 无法复现、缺少证据、描述含糊。\n"
                 "- 低危自评（仅扫描器结果、无实际危害证明）。\n"
                 "- 重复提交或已公开已知问题。\n"
                 "- 使用自动化扫描产生大量脏数据、影响业务稳定性。",
         },
        {"heading": "4. 提交与跟进节奏",
         "body": "- 提交后在平台内及时关注审核状态与厂商补充信息请求。\n"
                 "- 被要求补充时，优先提供最小化可复现证据。\n"
                 "- 修复后配合厂商复测，确认闭环再关闭。",
         },
    ],
}

# 合规风险提示
_COMPLIANCE: dict = {
    "title": "合规与授权风险提示",
    "authorization_scope": "仅在目标 SRC 平台明确公示的授权范围内开展测试：授权域名/IP、"
                           "指定 App/小程序、白名单测试账号、约定的测试时段与禁止项。",
    "sections": [
        {"heading": "1. 授权范围声明",
         "body": "所有测试必须基于平台公示的授权范围与《众测协议》。范围外的一切探测、"
                 "扫描、利用行为均视为未授权，可能触犯《网络安全法》《刑法》第 285/286 条。"
                 "本平台仅提供任务登记与流程管理，不构成任何测试授权。",
         },
        {"heading": "2. 禁止行为（红线）",
         "body": "- 禁止对范围外目标进行任何形式的探测与攻击。\n"
                 "- 禁止破坏数据、植入后门、反弹 shell、持久化控制。\n"
                 "- 禁止获取、下载、传播真实用户隐私数据与商业机密。\n"
                 "- 禁止使用真实资金进行支付类逻辑验证（用测试账号/沙箱）。\n"
                 "- 禁止 DDoS、批量轰炸、影响业务可用性的行为。",
         },
        {"heading": "3. 数据处理与保密",
         "body": "测试中接触的敏感数据须最小化获取、及时删除；证据文件中的个人信息需脱敏；"
                 "不得对外披露漏洞细节直至厂商修复并授权公开。",
         },
        {"heading": "4. 责任与免责",
         "body": "本平台为内部流程与收益记录工具，收益为站内记账口径（不涉及真实资金划转）。"
                 "使用者须自行确保测试行为合法合规，因超出授权范围导致的一切法律后果由行为人自行承担。",
         },
    ],
}


@router.get("/articles")
async def list_articles(keyword: str | None = None,
                        category: str | None = None,
                        _: User = Depends(get_current_user)):
    """漏洞知识库文章列表（按关键词/分类筛选）。"""
    items = _ARTICLES
    if category:
        items = [a for a in items if a["category"] == category]
    if keyword:
        kw = keyword.lower()
        items = [a for a in items
                 if kw in a["title"].lower() or kw in a["summary"].lower()
                 or kw in a["cwe"].lower() or kw in a["detail"].lower()]
    return {"items": items, "total": len(items),
            "categories": sorted({a["category"] for a in _ARTICLES})}


@router.get("/articles/{article_id}")
async def get_article(article_id: str, _: User = Depends(get_current_user)):
    for a in _ARTICLES:
        if a["id"] == article_id:
            return a
    raise HTTPException(404, "文章不存在")


@router.get("/guidelines")
async def get_guidelines(_: User = Depends(get_current_user)):
    """提交规范指引。"""
    return _GUIDELINES


@router.get("/compliance")
async def get_compliance(_: User = Depends(get_current_user)):
    """合规风险提示与授权范围声明。"""
    return _COMPLIANCE
