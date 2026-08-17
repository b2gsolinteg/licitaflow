from pathlib import Path


APP = Path(__file__).resolve().parents[1] / "app.py"
text = APP.read_text(encoding="utf-8")


def replace_once(old, new, label):
    global text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: esperado 1 trecho, encontrado {count}")
    text = text.replace(old, new, 1)


replace_once(
    '                    remember = st.checkbox("Lembrar de mim", value=True)\n',
    '',
    "checkbox lembrar de mim",
)

replace_once(
    '                    st.markdown(\'<div class="ln-forgot">Esqueceu a senha?</div>\', unsafe_allow_html=True)\n',
    '                    st.markdown(\'<div class="ln-forgot"><a href="?auth=recovery">Esqueceu a senha?</a></div>\', unsafe_allow_html=True)\n',
    "link de recuperação",
)

forgot_css = '''        .ln-forgot {
            text-align:right;margin-top:-2.1rem;margin-bottom:1.15rem;padding-right:.1rem;
            font-size:.78rem;color:#C8870C;position:relative;z-index:4;pointer-events:none;
        }
'''
forgot_css_new = '''        .ln-forgot {
            text-align:right;margin-top:-2.1rem;margin-bottom:1.15rem;padding-right:.1rem;
            font-size:.78rem;color:#C8870C;position:relative;z-index:4;
        }
        .ln-forgot a {color:#C8870C !important;text-decoration:none;font-weight:700;}
        .ln-forgot a:hover {text-decoration:underline;}
'''
replace_once(forgot_css, forgot_css_new, "CSS do link de recuperação")

marker = '''        /* ====================================================
           LICITANEXO - PATCH MENU LATERAL
           ==================================================== */'''
positions = []
start = 0
while True:
    position = text.find(marker, start)
    if position < 0:
        break
    positions.append(position)
    start = position + len(marker)

if len(positions) != 2:
    raise RuntimeError(
        f"bloco CSS duplicado: esperado 2 marcadores, encontrado {len(positions)}"
    )

first, second = positions
style_end = text.find("</style>", second)
if style_end < 0:
    raise RuntimeError("fechamento </style> não encontrado após CSS duplicado")

first_block = text[first:second].strip()
second_block = text[second:style_end].strip()
if first_block != second_block:
    raise RuntimeError("os dois blocos CSS não são idênticos; patch abortado")

text = text[:second] + text[style_end:]

if 'remember = st.checkbox("Lembrar de mim"' in text:
    raise RuntimeError("checkbox de sessão persistente ainda presente")
if text.count(marker) != 1:
    raise RuntimeError("CSS lateral não foi deduplicado corretamente")
if 'href="?auth=recovery"' not in text:
    raise RuntimeError("link de recuperação não foi aplicado")

APP.write_text(text, encoding="utf-8")
print("APP_HARDENING_PATCH=PASS")
