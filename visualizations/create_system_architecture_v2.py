"""
CQOx System Architecture Diagram - Dark Theme
Shows the complete technical stack and component interactions
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
import matplotlib.lines as mlines
from diagram_config import setup_japanese_font, DARK_THEME, FONT_SIZES, setup_dark_theme, get_text_kwargs

# Setup Japanese font (for consistency, though not used in this diagram)
japanese_font = setup_japanese_font()

# Increased figure size by 18%
fig, ax = plt.subplots(1, 1, figsize=(26, 18.8))
ax.set_xlim(0, 22)
ax.set_ylim(0, 16)
ax.axis('off')

# Apply dark theme
setup_dark_theme(fig, ax)

# Title
ax.text(11, 15.5, 'CQOx System Architecture',
        **get_text_kwargs(None, 'title', weight='bold'), ha='center')
ax.text(11, 14.8, 'Production-Ready Causal Inference Platform',
        **get_text_kwargs(None, 'subtitle', DARK_THEME['text_secondary']),
        ha='center', style='italic')

# === Layer 1: Frontend (Top) ===
y_frontend = 12.5
frontend_box = FancyBboxPatch((1, y_frontend), 20, 1.8, boxstyle="round,pad=0.15",
                              edgecolor=DARK_THEME['accent_blue'], facecolor=DARK_THEME['box_data'],
                              alpha=0.7, linewidth=3)
ax.add_patch(frontend_box)
ax.text(11, y_frontend+1.5, 'Frontend Layer',
        **get_text_kwargs(None, 'heading', weight='bold'), ha='center')
ax.text(11, y_frontend+1.15, 'React 18 + TypeScript + Vite',
        **get_text_kwargs(None, 'label', DARK_THEME['text_secondary']),
        ha='center', style='italic')

# Frontend components
components_y = y_frontend + 0.3
components = [
    ('Dataset Mgmt', 2), ('Causal Design', 4.5), ('Diagnostics', 7),
    ('Decision Console', 9.5), ('Portfolio', 12), ('Digital Twin', 14.5),
    ('Policy Lab', 17), ('Governance', 19.5)
]
for comp_name, comp_x in components:
    comp_box = Rectangle((comp_x-0.8, components_y), 1.6, 0.6,
                          edgecolor=DARK_THEME['accent_blue'], facecolor=DARK_THEME['box_data'],
                          alpha=0.9, linewidth=1.5)
    ax.add_patch(comp_box)
    ax.text(comp_x, components_y+0.3, comp_name,
            **get_text_kwargs(None, 'body', weight='bold'),
            ha='center', va='center')

# TanStack Query label
ax.text(11, y_frontend+0.05, 'State Management: TanStack Query v5 + React Context',
        **get_text_kwargs(None, 'label', DARK_THEME['accent_blue']),
        ha='center', style='italic')

# === Layer 2: API Gateway ===
y_api = 10
api_box = FancyBboxPatch((1, y_api), 20, 1.5, boxstyle="round,pad=0.15",
                         edgecolor=DARK_THEME['accent_green'], facecolor=DARK_THEME['box_decision'],
                         alpha=0.7, linewidth=3)
ax.add_patch(api_box)
ax.text(11, y_api+1.2, 'API Layer - FastAPI 0.104+',
        **get_text_kwargs(None, 'heading', weight='bold'), ha='center')
ax.text(11, y_api+0.85, 'Async ASGI Server (Uvicorn)',
        **get_text_kwargs(None, 'label', DARK_THEME['text_secondary']),
        ha='center', style='italic')

# API endpoints
endpoints_y = y_api + 0.2
endpoints = [
    ('/datasets', 2.5), ('/causal', 5), ('/decisions', 7.5),
    ('/portfolio', 10), ('/twin', 12.5), ('/governance', 15),
    ('/export', 17.5), ('/auth', 19.5)
]
for ep_name, ep_x in endpoints:
    ep_box = Rectangle((ep_x-0.9, endpoints_y), 1.8, 0.5,
                        edgecolor=DARK_THEME['accent_green'], facecolor=DARK_THEME['box_decision'],
                        alpha=0.9, linewidth=1.5)
    ax.add_patch(ep_box)
    ax.text(ep_x, endpoints_y+0.25, ep_name,
            **get_text_kwargs(None, 'detail'),
            ha='center', va='center', family='monospace')

# Arrows: Frontend -> API
for _, comp_x in components:
    arrow = FancyArrowPatch((comp_x, y_frontend+0.25), (comp_x, y_api+1.55),
                           arrowstyle='->', mutation_scale=15, linewidth=1.5,
                           color=DARK_THEME['text_secondary'], alpha=0.5, linestyle='dashed')
    ax.add_patch(arrow)

# === Layer 3: Business Logic ===
y_logic = 7.2
logic_box = FancyBboxPatch((1, y_logic), 9, 2.2, boxstyle="round,pad=0.15",
                           edgecolor=DARK_THEME['accent_red'], facecolor=DARK_THEME['box_governance'],
                           alpha=0.6, linewidth=2)
ax.add_patch(logic_box)
ax.text(5.5, y_logic+1.9, 'Core Business Logic',
        **get_text_kwargs(None, 'heading', weight='bold'), ha='center')

# Core modules
modules = [
    ('Causal Engine\n7 Estimators', 2.5, y_logic+1.2),
    ('Portfolio\nOptimizer', 5.5, y_logic+1.2),
    ('Digital Twin\nSimulator', 8.2, y_logic+1.2),
    ('CAS Scoring', 2.5, y_logic+0.3),
    ('Policy\nGenerator', 5.5, y_logic+0.3),
    ('Export\nGate', 8.2, y_logic+0.3)
]
for mod_name, mod_x, mod_y in modules:
    mod_box = Rectangle((mod_x-0.9, mod_y-0.35), 1.8, 0.7,
                        edgecolor=DARK_THEME['accent_red'], facecolor=DARK_THEME['box_governance'],
                        alpha=0.9, linewidth=1.5)
    ax.add_patch(mod_box)
    ax.text(mod_x, mod_y, mod_name,
            **get_text_kwargs(None, 'detail', weight='bold'),
            ha='center', va='center')

# === Layer 4: Async Task Processing ===
y_celery = 7.2
celery_box = FancyBboxPatch((11.5, y_celery), 9.3, 2.2, boxstyle="round,pad=0.15",
                            edgecolor=DARK_THEME['accent_red'], facecolor=DARK_THEME['box_governance'],
                            alpha=0.6, linewidth=2)
ax.add_patch(celery_box)
ax.text(16.15, y_celery+1.9, 'Async Task Processing - Celery',
        **get_text_kwargs(None, 'heading', weight='bold'), ha='center')

# Celery tasks
tasks = [
    ('Model Training\nTask', 13, y_celery+1.2),
    ('Diagnostic\nTask', 15.5, y_celery+1.2),
    ('Portfolio\nCalc Task', 18, y_celery+1.2),
    ('Export\nTask', 13, y_celery+0.3),
    ('Simulation\nTask', 15.5, y_celery+0.3),
    ('Notification\nTask', 18, y_celery+0.3)
]
for task_name, task_x, task_y in tasks:
    task_box = Rectangle((task_x-0.9, task_y-0.35), 1.8, 0.7,
                         edgecolor=DARK_THEME['accent_red'], facecolor=DARK_THEME['box_governance'],
                         alpha=0.9, linewidth=1.5)
    ax.add_patch(task_box)
    ax.text(task_x, task_y, task_name,
            **get_text_kwargs(None, 'detail', weight='bold'),
            ha='center', va='center')

# === Layer 5: Data & Infrastructure ===
y_data = 4
# PostgreSQL
pg_box = FancyBboxPatch((1.5, y_data), 4, 2.2, boxstyle="round,pad=0.15",
                        edgecolor=DARK_THEME['accent_blue'], facecolor=DARK_THEME['box_data'],
                        alpha=0.7, linewidth=2.5)
ax.add_patch(pg_box)
ax.text(3.5, y_data+1.8, 'PostgreSQL 15',
        **get_text_kwargs(None, 'heading', weight='bold'), ha='center')
ax.text(3.5, y_data+1.45, '+ TimescaleDB',
        **get_text_kwargs(None, 'label', DARK_THEME['text_secondary']),
        ha='center', style='italic')
ax.text(3.5, y_data+0.9, 'Tables:',
        **get_text_kwargs(None, 'label', weight='bold'), ha='center')
tables = ['datasets', 'causal_designs', 'analysis_results', 'decisions', 'policies', 'users']
for i, table in enumerate(tables):
    row = i // 2
    col = i % 2
    ax.text(2.5 + col*2, y_data+0.5 - row*0.3, f'• {table}',
            **get_text_kwargs(None, 'detail'), ha='left')

# Redis
redis_box = FancyBboxPatch((6.5, y_data), 3.5, 2.2, boxstyle="round,pad=0.15",
                           edgecolor=DARK_THEME['accent_red'], facecolor=DARK_THEME['box_governance'],
                           alpha=0.6, linewidth=2.5)
ax.add_patch(redis_box)
ax.text(8.25, y_data+1.8, 'Redis 7',
        **get_text_kwargs(None, 'heading', weight='bold'), ha='center')
ax.text(8.25, y_data+1.45, 'Cache & Session',
        **get_text_kwargs(None, 'label', DARK_THEME['text_secondary']),
        ha='center', style='italic')
ax.text(8.25, y_data+0.9, 'Usage:',
        **get_text_kwargs(None, 'label', weight='bold'), ha='center')
uses = ['API Response Cache', 'Session Store', 'Rate Limiting', 'Celery Result']
for i, use in enumerate(uses):
    ax.text(8.25, y_data+0.5 - i*0.3, f'• {use}',
            **get_text_kwargs(None, 'detail'), ha='center')

# RabbitMQ
rmq_box = FancyBboxPatch((11, y_data), 3.5, 2.2, boxstyle="round,pad=0.15",
                         edgecolor=DARK_THEME['accent_orange'], facecolor=DARK_THEME['box_export'],
                         alpha=0.7, linewidth=2.5)
ax.add_patch(rmq_box)
ax.text(12.75, y_data+1.8, 'RabbitMQ 3',
        **get_text_kwargs(None, 'heading', weight='bold'), ha='center')
ax.text(12.75, y_data+1.45, 'Message Broker',
        **get_text_kwargs(None, 'label', DARK_THEME['text_secondary']),
        ha='center', style='italic')
ax.text(12.75, y_data+0.9, 'Queues:',
        **get_text_kwargs(None, 'label', weight='bold'), ha='center')
queues = ['causal_analysis', 'portfolio_calc', 'exports', 'notifications']
for i, queue in enumerate(queues):
    ax.text(12.75, y_data+0.5 - i*0.3, f'• {queue}',
            **get_text_kwargs(None, 'detail'), ha='center')

# S3 / Object Storage
s3_box = FancyBboxPatch((15.5, y_data), 3, 2.2, boxstyle="round,pad=0.15",
                        edgecolor=DARK_THEME['accent_green'], facecolor=DARK_THEME['box_decision'],
                        alpha=0.6, linewidth=2.5)
ax.add_patch(s3_box)
ax.text(17, y_data+1.8, 'Object Storage',
        **get_text_kwargs(None, 'heading', weight='bold'), ha='center')
ax.text(17, y_data+1.45, 'S3 / MinIO',
        **get_text_kwargs(None, 'label', DARK_THEME['text_secondary']),
        ha='center', style='italic')
ax.text(17, y_data+0.9, 'Stored:',
        **get_text_kwargs(None, 'label', weight='bold'), ha='center')
stored = ['Uploaded CSVs', 'Model Artifacts', 'Export Files', 'Logs']
for i, item in enumerate(stored):
    ax.text(17, y_data+0.5 - i*0.3, f'• {item}',
            **get_text_kwargs(None, 'detail'), ha='center')

# === Layer 6: External Integrations ===
y_external = 1.2
ext_box = FancyBboxPatch((1, y_external), 20, 1.5, boxstyle="round,pad=0.15",
                         edgecolor=DARK_THEME['accent_purple'], facecolor=DARK_THEME['box_causal'],
                         alpha=0.5, linewidth=2)
ax.add_patch(ext_box)
ax.text(11, y_external+1.15, 'External Integrations',
        **get_text_kwargs(None, 'heading', weight='bold'), ha='center')

externals = [
    ('MA Tools\n(KARTE)', 3), ('CDP\n(Salesforce)', 6.5), ('BI Tools\n(Tableau)', 10),
    ('Monitoring\n(Prometheus)', 13.5), ('Logging\n(ELK)', 17), ('Auth\n(OAuth2)', 20)
]
for ext_name, ext_x in externals:
    ext_small_box = Rectangle((ext_x-1, y_external+0.15), 2, 0.7,
                              edgecolor=DARK_THEME['accent_purple'], facecolor=DARK_THEME['box_causal'],
                              alpha=0.9, linewidth=1.5, linestyle='dashed')
    ax.add_patch(ext_small_box)
    ax.text(ext_x, y_external+0.5, ext_name,
            **get_text_kwargs(None, 'body'), ha='center', va='center')

# === Arrows: Connections ===
# API -> Business Logic
arrow1 = FancyArrowPatch((5.5, y_api-0.05), (5.5, y_logic+2.25),
                        arrowstyle='<->', mutation_scale=20, linewidth=2.5,
                        color=DARK_THEME['accent_green'])
ax.add_patch(arrow1)

# API -> Celery
arrow2 = FancyArrowPatch((14, y_api-0.05), (16, y_celery+2.25),
                        arrowstyle='<->', mutation_scale=20, linewidth=2.5,
                        color=DARK_THEME['accent_red'])
ax.add_patch(arrow2)

# Business Logic -> PostgreSQL
arrow3 = FancyArrowPatch((3.5, y_logic-0.05), (3.5, y_data+2.25),
                        arrowstyle='<->', mutation_scale=20, linewidth=2.5,
                        color=DARK_THEME['accent_blue'])
ax.add_patch(arrow3)

# Celery -> RabbitMQ
arrow4 = FancyArrowPatch((16, y_celery-0.05), (13, y_data+2.25),
                        arrowstyle='<->', mutation_scale=20, linewidth=2.5,
                        color=DARK_THEME['accent_orange'])
ax.add_patch(arrow4)

# API -> Redis
arrow5 = FancyArrowPatch((8.5, y_api-0.05), (8.25, y_data+2.25),
                        arrowstyle='<->', mutation_scale=20, linewidth=2.5,
                        color=DARK_THEME['accent_red'])
ax.add_patch(arrow5)

# Export -> External
arrow6 = FancyArrowPatch((8.5, y_logic-0.05), (6, y_external+1.6),
                        arrowstyle='->', mutation_scale=20, linewidth=2,
                        color=DARK_THEME['accent_purple'], linestyle='dashed')
ax.add_patch(arrow6)

# === Security & Compliance Box ===
security_box = FancyBboxPatch((19.3, 10), 2.5, 4, boxstyle="round,pad=0.1",
                              edgecolor=DARK_THEME['accent_red'], facecolor=DARK_THEME['box_governance'],
                              alpha=0.8, linewidth=2)
ax.add_patch(security_box)
ax.text(20.55, 13.7, 'Security',
        **get_text_kwargs(None, 'label', weight='bold'), ha='center')
ax.text(20.55, 13.35, '& Compliance',
        **get_text_kwargs(None, 'label', weight='bold'), ha='center')
security_features = [
    'JWT Auth',
    'RBAC',
    'Row-Level\nSecurity',
    'Audit Log',
    'HTTPS/TLS',
    'Rate Limit',
    'GDPR'
]
for i, feature in enumerate(security_features):
    ax.text(20.55, 12.8 - i*0.45, f'✓ {feature}',
            **get_text_kwargs(None, 'detail'), ha='center')

# === Technology Stack Legend ===
legend_y = 0.3
ax.text(1, legend_y, 'Tech Stack:',
        **get_text_kwargs(None, 'label', weight='bold'))
stack = [
    'Frontend: React 18 + TypeScript + Vite + TanStack Query',
    'Backend: FastAPI 0.104+ (Python 3.11+) + Uvicorn ASGI',
    'Database: PostgreSQL 15 + TimescaleDB (Time-series)',
    'Cache: Redis 7 (Cache + Session)',
    'Queue: RabbitMQ 3 + Celery (Async Tasks)',
    'Storage: S3/MinIO (Object Storage)',
    'Deployment: Docker + Kubernetes + ArgoCD (GitOps)'
]
for i, tech in enumerate(stack):
    ax.text(1.2, legend_y - 0.25 - i*0.15, f'• {tech}',
            **get_text_kwargs(None, 'detail'), family='monospace')

# Add deployment info
ax.text(11, 0.25, 'Production Deployment: Kubernetes + Helm + ArgoCD | Monitoring: Prometheus + Grafana | Logging: ELK Stack',
        **get_text_kwargs(None, 'body', DARK_THEME['text_secondary']),
        ha='center', style='italic',
        bbox=dict(boxstyle='round,pad=0.5', facecolor=DARK_THEME['accent_yellow'], alpha=0.3))

plt.tight_layout()
plt.savefig('/home/hirokionodera/CQOx_gen/Picture/system_architecture.png',
            dpi=300, bbox_inches='tight', facecolor=DARK_THEME['background'])
print("✓ System Architecture diagram created: Picture/system_architecture.png")
