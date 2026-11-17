[17:21, 17/11/2026] Sarotto: import streamlit as st
import pandas as pd
import tempfile
from fpdf import FPDF
from PIL import Image
import os
from datetime import datetime

# Configuracao visual da pagina
st.set_page_config(page_title="RDO Digital - Minerva", layout="wide", page_icon="🏗️")

# Nome do arquivo que vai guardar os dados (Banco de Dados local)
ARQUIVO_EXCEL = "Banco_Dados_Obra_Minerva.xlsx"

# Funcao para salvar os dados nas abas do Excel sem apagar os anteriores
def salvar_dados(nova_linha_df, nome_aba):
    if os.path.exists(ARQUIVO_EXCEL):
        with pd.ExcelFile(ARQUIVO_EXCEL) as xls:
            abas_existentes = {sheet: pd.read_excel(xls, sheet) for sheet in xls.sheet_names}
    else:
        abas_existentes = {}

    if nome_aba in abas_existentes:
        abas_exist…
[17:25, 17/11/2026] Sarotto: import io
import os
import tempfile
from datetime import datetime
from fpdf import FPDF
import pandas as pd
from PIL import Image
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# Configuracao visual da pagina
st.set_page_config(page_title="RDO Digital - Minerva", layout="wide", page_icon="🏗️")

# Conexao com o Google Sheets (usando o link salvo nos Secrets)
conn = st.connection("gsheets", type=GSheetsConnection)


# Funcao para ler os dados salvos no Google Sheets
def carregar_dados(nome_aba):
    try:
        df = conn.read(worksheet=nome_aba, ttl=0)
        return df.dropna(how="all")
    except Exception:
        return pd.DataFrame()


# Funcao para salvar novos registros no Google Sheets sem apagar os anteriores
def salvar_dados(nova_linha_df, nome_aba):
    df_atual = carregar_dados(nome_aba)
    if not df_atual.empty:
        df_atualizado = pd.concat([df_atual, nova_linha_df], ignore_index=True)
    else:
        df_atualizado = nova_linha_df
    conn.update(worksheet=nome_aba, data=df_atualizado)


# Funcao para sobrescrever uma aba inteira (usada ao editar ou excluir)
def sobrescrever_aba(df_novo, nome_aba):
    conn.update(worksheet=nome_aba, data=df_novo)


# --- CABECALHO DO SISTEMA ---
st.title("🏗️ RDO Digital/Gestão de Campo")
st.markdown("Obra: Jardins de Nazaré | Construtora Minerva | Engenharia 4.0")
st.divider()

# --- MENU DE ABAS ---
aba1, aba2, aba3, aba4, aba5 = st.tabs([
    "📋 RDO/Clima",
    "👷 Equipes/Apartamentos",
    "🚛 Concretagem",
    "📌 RNC (Qualidade)",
    "📊 Painel do Coordenador"
])

# ==========================================
# ABA 1: RDO DIÁRIO E CLIMA REAL
# ==========================================
with aba1:
    st.subheader("Registro Diário de Obra")
    col1, col2, col3 = st.columns(3)
    with col1:
        data_rdo = st.date_input("Data", datetime.today())
    with col2:
        clima_m = st.selectbox("Clima Manhã (Real)", ["Bom / Sol", "Nublado", "Chuva Fraca", "Chuva Forte"])
    with col3:
        clima_t = st.selectbox("Clima Tarde (Real)", ["Bom / Sol", "Nublado", "Chuva Fraca", "Chuva Forte"])

    condicao = st.radio(
        "Condição de Trabalho no Canteiro",
        ["Praticável", "Parcialmente Impraticável", "Totalmente Impraticável"],
        horizontal=True
    )

    horas_chuva = 0.0
    if "Chuva" in clima_m or "Chuva" in clima_t:
        horas_chuva = st.number_input("Quantas horas a obra ficou parada por chuva?", min_value=0.0, max_value=12.0, step=0.5)

    empresas = st.multiselect("Empresas / Visitas Técnicas Presentes", [
        "Equipe Própria Minerva",
        "Cerqueira (Empreiteira)",
        "Saint-Gobain (Monocapa)",
        "Fiscalização / Prefeitura",
        "Outros Fornecedores"
    ])
    obs_visitas = st.text_input("Detalhes das visitas (Ex: Técnico da Saint-Gobain validou fachada norte)")
    atividades = st.text_area("Resumo das Atividades Executadas Hoje")

    if st.button("Salvar RDO do Dia", type="primary"):
        df_rdo = pd.DataFrame([{
            "Data": data_rdo.strftime("%d/%m/%Y"),
            "Clima_Manha": clima_m,
            "Clima_Tarde": clima_t,
            "Condicao": condicao,
            "Horas_Paradas": horas_chuva,
            "Terceiros": ", ".join(empresas),
            "Obs_Visitas": obs_visitas,
            "Atividades": atividades
        }])
        salvar_dados(df_rdo, "RDO_Diario")
        st.success("✅ RDO salvo na nuvem com sucesso!")

# ==========================================
# ABA 2: ALOCAÇÃO DE EQUIPES POR APARTAMENTO
# ==========================================
with aba2:
    st.subheader("Rastreabilidade de Equipes por Pavimento/Unidade")
    c1, c2, c3 = st.columns(3)
    with c1:
        colab = st.text_input("Nome do Colaborador ou Líder de Equipe")
        emp_colab = st.selectbox("Empresa", ["Construtora Minerva", "Cerqueira", "Saint-Gobain", "Outra"])
    with c2:
        pav = st.selectbox("Pavimento", [
            "Subsolo", "Térreo", "1º Pavimento", "2º Pavimento", "3º Pavimento",
            "4º Pavimento", "5º Pavimento", "6º Pavimento", "7º Pavimento",
            "8º Pavimento", "9º Pavimento", "Cobertura", "Fachada"
        ])
        apto = st.text_input("Apartamento ou Local (Ex: Apto 102, Hall)")
    with c3:
        serv = st.selectbox("Serviço Executado", [
            "Alvenaria", "Monocapa", "Contrapiso", "Hidráulica", "Elétrica",
            "Impermeabilização", "Gesso", "Drywall", "Carpintaria", "Pintura"
        ])
        status_serv = st.selectbox("Status", ["Iniciado", "Em Andamento", "Concluído"])

    if st.button("Registrar Alocação de Equipe"):
        df_eq = pd.DataFrame([{
            "Data": datetime.today().strftime("%d/%m/%Y"),
            "Colaborador": colab,
            "Empresa": emp_colab,
            "Pavimento": pav,
            "Unidade": apto,
            "Servico": serv,
            "Status": status_serv
        }])
        salvar_dados(df_eq, "Alocacao_Equipes")
        st.success(f"✅ {colab} registrado no {pav} ({apto})!")

# ==========================================
# ABA 3: CONTROLE DE CONCRETAGEM
# ==========================================
with aba3:
    st.subheader("Recebimento de Concreto Usinado")
    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        concreteira = st.text_input("Concreteira (Ex: Polimix, Votorantim)")
        nf = st.text_input("Número da Nota Fiscal / Ticket")
    with cc2:
        peca = st.text_input("Peça Concretada (Ex: Pilares 2º Pav)")
        fck = st.selectbox("FCK de Projeto (MPa)", [20, 25, 30, 35, 40])
    with cc3:
        vol_m3 = st.number_input("Volume (m³)", min_value=0.5, step=0.5)
        slump = st.number_input("Slump Obtido na Obra (cm)", min_value=1, max_value=30, value=12)

    status_conc = st.radio("Status do Recebimento", ["Aprovado", "Aprovado com Aditivo", "Recusado"], horizontal=True)

    if st.button("Salvar Caminhão de Concreto"):
        df_conc = pd.DataFrame([{
            "Data": datetime.today().strftime("%d/%m/%Y"),
            "Concreteira": concreteira,
            "NF": nf,
            "Peca": peca,
            "FCK": fck,
            "Volume_m3": vol_m3,
            "Slump_cm": slump,
            "Status": status_conc
        }])
        salvar_dados(df_conc, "Concretagem")
        st.success(f"✅ Caminhão NF {nf} ({vol_m3} m³) registrado!")

# ==========================================
# ABA 4: RNC (CONTROLE DE QUALIDADE)
# ==========================================
with aba4:
    st.subheader("Registro de Não Conformidade (RNC)")
    ci1, ci2 = st.columns(2)
    with ci1:
        local_issue = st.text_input("Local da Não Conformidade (Ex: Pilar P14 - Térreo)")
        disc_issue = st.selectbox("Disciplina", [
            "Estrutura", "Alvenaria", "Monocapa / Fachada", "Instalações",
            "Drywall", "Carpintaria", "Contrapiso", "Segurança do Trabalho"
        ])
    with ci2:
        resp_issue = st.selectbox("Responsável pela Correção", ["Mestre de Obras", "Cerqueira", "Saint-Gobain", "Equipe Minerva"])
        prazo_issue = st.date_input("Prazo Limite para Correção")

    desc_issue = st.text_area("Descrição detalhada do problema")

    if st.button("Abrir RNC de Qualidade"):
        df_iss = pd.DataFrame([{
            "Data_Abertura": datetime.today().strftime("%d/%m/%Y"),
            "Local": local_issue,
            "Disciplina": disc_issue,
            "Descricao": desc_issue,
            "Responsavel": resp_issue,
            "Prazo": prazo_issue.strftime("%d/%m/%Y"),
            "Status": "Aberto"
        }])
        salvar_dados(df_iss, "Issues")
        st.warning(f"📌 RNC aberta e atribuída para: {resp_issue}")

# ==========================================
# ABA 5: PAINEL DO COORDENADOR (VISUALIZAÇÃO)
# ==========================================
with aba5:
    st.subheader("📊 Visão Gerencial em Tempo Real")
    st.info("Aqui o Coordenador acompanha todos os registros lançados na obra, edita células se necessário e baixa relatórios.")

    tab_v1, tab_v2, tab_v3, tab_v4 = st.tabs(["Histórico RDO", "Mapa de Equipes", "Concretagem", "RNCs Abertas"])

    def exibir_tabela_editavel(nome_aba, chave_unica):
        df_atual = carregar_dados(nome_aba)
        if not df_atual.empty:
            st.caption("💡 Dê um clique duplo em qualquer célula abaixo para corrigir um texto e depois clique em Salvar.")
            df_editado = st.data_editor(df_atual, use_container_width=True, key=chave_unica)
            if st.button(f"💾 Salvar alterações em {nome_aba}", key=f"btn_{chave_unica}"):
                sobrescrever_aba(df_editado, nome_aba)
                st.success("Alterações salvas na nuvem com sucesso!")
                st.rerun()
        else:
            st.info("Nenhum registro cadastrado nesta aba ainda.")

    with tab_v1:
        exibir_tabela_editavel("RDO_Diario", "edit_rdo")
    with tab_v2:
        exibir_tabela_editavel("Alocacao_Equipes", "edit_equipes")
    with tab_v3:
        df_c = carregar_dados("Concretagem")
        if not df_c.empty and "Volume_m3" in df_c.columns:
            st.metric("Volume Total Concretado (m³)", f"{pd.to_numeric(df_c['Volume_m3'], errors='coerce').sum():.2f} m³")
        exibir_tabela_editavel("Concretagem", "edit_concreto")
    with tab_v4:
        exibir_tabela_editavel("Issues", "edit_issues")

    # --- BLOCO DE EXCLUSÃO ---
    st.divider()
    st.subheader("🗑️ Excluir Registro")
    aba_escolhida = st.selectbox(
        "Escolha a categoria do registro:",
        ["RDO_Diario", "Alocacao_Equipes", "Concretagem", "Issues"]
    )
    df_exclusao = carregar_dados(aba_escolhida)

    if not df_exclusao.empty:
        opcoes = [f"Linha {i} | {row.iloc} - {row.iloc}" for i, row in df_exclusao.iterrows()]
        selecionado = st.selectbox("Selecione o registro para apagar:", opcoes)

        if st.button("Excluir Registro Selecionado", type="primary"):
            indice = int(selecionado.split(" "))