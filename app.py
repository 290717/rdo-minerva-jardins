import io
import os
import tempfile
from datetime import datetime
from fpdf import FPDF
import pandas as pd
from PIL import Image
import streamlit as st
from supabase import create_client

# Configuração visual da página
st.set_page_config(page_title="RDO Digital - Minerva", layout="wide", page_icon="🏗️")


# Conexão com o Supabase
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


supabase = init_connection()


def carregar_dados(nome_tabela):
    try:
        res = supabase.table(nome_tabela).select("*").order("id").execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            colunas_dados = list(c for c in df.columns if c != "id")
            df = df.dropna(how="all", subset=colunas_dados)
            df = df[~(df[colunas_dados].astype(str).apply(lambda x: x.str.strip() == "").all(axis=1))]
        return df
    except Exception:
        return pd.DataFrame()


def salvar_dados(dados_dict, nome_tabela):
    try:
        supabase.table(nome_tabela).insert(dados_dict).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar no banco ({nome_tabela}): {e}")
        return False


def criar_pdf_rdo(df_dados, lista_fotos):
    pdf = FPDF()
    pdf.add_page()

    # Cabeçalho do Relatório
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "RELATORIO DIARIO DE OBRA (RDO) - MINERVA", ln=True, align="C")
    pdf.ln(5)

    # Pega o último RDO lançado no banco
    if not df_dados.empty:
        ultimo_rdo = df_dados.drop(columns="id", errors="ignore").iloc[-1]
        pdf.set_font("Arial", size=11)

        for coluna, valor in ultimo_rdo.items():
            texto = f"{coluna}: {valor}".encode("latin-1", "replace").decode("latin-1")
            pdf.multi_cell(0, 8, texto)
            pdf.ln(1)
    else:
        pdf.set_font("Arial", size=11)
        pdf.cell(0, 10, "Nenhum dado de RDO registrado na planilha ainda.", ln=True)

    # Seção de Fotos Anexadas
    if lista_fotos:
        pdf.ln(5)
        pdf.set_font("Arial", "B", 13)
        pdf.cell(0, 10, "REGISTRO FOTOGRAFICO DE CAMPO:", ln=True)
        pdf.ln(3)

        for foto in lista_fotos:
            img = Image.open(foto)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                img.save(tmp.name, format="JPEG")
                if pdf.get_y() > 190:
                    pdf.add_page()
                pdf.image(tmp.name, x=15, w=120)
                pdf.ln(5)
            os.unlink(tmp.name)

    return bytes(pdf.output())


# --- CABEÇALHO DO SISTEMA ---
# --- CABEÇALHO DO SISTEMA ---
col_titulo, col_imagem = st.columns([3, 1.5], vertical_alignment="center")

with col_titulo:
    st.title("RDO Digital/Gestão de Campo")
    st.markdown("Obra: Jardins de Nazaré | Construtora Minerva |Engenharia 4.0 - 👷🏽‍♀️Sara Elienai")

with col_imagem:
    st.image("predio Nazaré.jpg", use_container_width=True)   # Ajuste o valor de 'width' para aumentar ou diminuir

st.divider()
# --- MENU DE ABAS ---
# --- BARRA LATERAL (MENU DE NAVEGAÇÃO) ---
with st.sidebar:
    st.image("predio Nazaré.jpg", use_container_width=True)
    st.markdown("### Construtora Minerva")
    st.caption("Obra: Jardins de Nazaré")
    st.divider()

    pagina = st.sidebar.radio(
        "Navegação",
        (
            "📋 RDO / Clima",
            "👷 Equipes / Apartamentos",
            "🚛 Concretagem",
            "📌 RNC (Qualidade)",
            "📊 Painel do Coordenador"
        ),
        label_visibility="collapsed"
    )

    st.divider()
    st.caption("Engenharia 4.0 - 👷🏽‍♀️ Sara Elienai")

# --- CABEÇALHO PRINCIPAL ---
st.title("🏗️ RDO Digital / Gestão de Campo")
st.divider()

# --- CONTEÚDO DE CADA PÁGINA ---
# --- CONTEÚDO DE CADA PÁGINA ---

# ==========================================
# ABA 1: RDO DIÁRIO E CLIMA REAL + PDF/FOTOS
# ==========================================
if pagina == "📋 RDO / Clima":
    st.subheader("Registro Diário de Obra")
    col1, col2, col3 = st.columns(3)
    # ... restante do código da aba 1 continua indentado aqui dentro ...

# ==========================================
# ABA 2: ALOCAÇÃO DE EQUIPES POR APARTAMENTO
# ==========================================
elif pagina == "👷 Equipes / Apartamentos":
    st.subheader("Rastreabilidade de Equipes por Pavimento/Unidade")
    # ... restante do código da aba 2 continua indentado aqui dentro ...

# ==========================================
# ABA 3: CONTROLE DE CONCRETAGEM
# ==========================================
elif pagina == "🚛 Concretagem":
    st.subheader("Recebimento de Concreto Usinado")
    # ... restante do código da aba 3 continua indentado aqui dentro ...

# ==========================================
# ABA 4: RNC (CONTROLE DE QUALIDADE)
# ==========================================
elif pagina == "📌 RNC (Qualidade)":
    st.subheader("Registro de Não Conformidade (RNC)")
    # ... restante do código da aba 4 continua indentado aqui dentro ...

ABA 5: PAINEL DO COORDENADOR (VISUALIZAÇÃO)


==========================================

elif pagina == "📊 Painel do Coordenador":
st.subheader("📊 Visão Gerencial em Tempo Real")
st.info("Dados sincronizados na nuvem. Dê dois cliques em qualquer célula para editar e clique em Salvar.")
tab_v1, tab_v2, tab_v3, tab_v4 = st.tabs(("Histórico RDO", "Mapa de Equipes", "Concretagem", "RNCs Abertas"))
def exibir_tabela_editavel(nome_tabela, chave_unica):
df_atual = carregar_dados(nome_tabela)
if not df_atual.empty:
df_atual = df_atual.reset_index(drop=True)
df_atual.insert(0, "Nº", range(1, len(df_atual) + 1))
df_editado = st.data_editor(
df_atual,
use_container_width=True,
disabled=("Nº", "id"),
hide_index=True,
column_config={"id": None},
key=chave_unica
)
if st.button(f"💾 Salvar alterações em {nome_tabela}", key=f"btn_{chave_unica}"):
df_limpo = df_editado.fillna("")
for _, row in df_limpo.iterrows():
dados_linha = {k: v for k, v in row.items() if k not in ("Nº", "id")}
supabase.table(nome_tabela).update(dados_linha).eq("id", int(row["id"])).execute()
st.success("Alterações salvas na nuvem!")
st.rerun()
else:
st.info("Nenhum registro cadastrado nesta aba ainda.")
with tab_v1:
exibir_tabela_editavel("rdo_diario", "edit_rdo")
with tab_v2:
exibir_tabela_editavel("alocacao_equipes", "edit_equipes")
with tab_v3:
df_c = carregar_dados("concretagem")
if not df_c.empty and "volume_m3" in df_c.columns:
st.metric("Volume Total Concretado (m³)", f"{pd.to_numeric(df_c['volume_m3'], errors='coerce').sum():.2f} m³")
exibir_tabela_editavel("concretagem", "edit_concreto")
with tab_v4:
exibir_tabela_editavel("issues", "edit_issues")
# --- BLOCO DE EXCLUSÃO ---
st.divider()
st.subheader("Excluir Registro")
aba_escolhida = st.selectbox(
"Escolha a categoria:",
("rdo_diario", "alocacao_equipes", "concretagem", "issues")
)
df_exclusao = carregar_dados(aba_escolhida)
if not df_exclusao.empty:
df_exclusao = df_exclusao.reset_index(drop=True)
mapa_ids = {}
opcoes = []
for idx, row in df_exclusao.iterrows():
num_visual = idx + 1
valores = list(row.drop("id", errors="ignore").values)
it = iter(valores)
col1_txt = next(it, "")
col2_txt = next(it, "")
rotulo = f"Nº {num_visual} | {col1_txt} - {col2_txt}"
opcoes.append(rotulo)
mapa_ids[rotulo] = int(row["id"])
selecionado = st.selectbox("Selecione o registro para apagar:", opcoes)
if st.button("Excluir Registro Selecionado", type="primary"):
id_real = mapa_ids[selecionado]
supabase.table(aba_escolhida).delete().eq("id", id_real).execute()
st.success("Registro excluído da nuvem!")
st.rerun()
else:
st.info("Nenhum registro cadastrado nesta categoria.")

    # --- BOTÃO PARA BAIXAR PLANILHA EXCEL COMPLETA ---
    st.divider()
    output_excel = io.BytesIO()
    with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
        tem_dados = False
        tabelas = {
            "RDO_Diario": "rdo_diario",
            "Equipes": "alocacao_equipes",
            "Concretagem": "concretagem",
            "RNC_Qualidade": "issues"
        }
        for aba_excel, nome_tab in tabelas.items():
            df_exp = carregar_dados(nome_tab)
            if not df_exp.empty:
                df_exp = df_exp.drop(columns="id", errors="ignore").reset_index(drop=True)
                df_exp.insert(0, "Nº", range(1, len(df_exp) + 1))
                df_exp.to_excel(writer, sheet_name=aba_excel, index=False)
                tem_dados = True

        if not tem_dados:
            pd.DataFrame({"Aviso": ("Nenhum dado cadastrado ainda.",)}).to_excel(
                writer, sheet_name="Sem_Dados", index=False
            )

    st.download_button(
        label="📥 Baixar Planilha Excel Completa (.xlsx)",
        data=output_excel.getvalue(),
        file_name=f"RDO_Minerva_{datetime.today().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )