import io
import os
import tempfile
from datetime import datetime
from fpdf import FPDF
import pandas as pd
from PIL import Image
import streamlit as st
from supabase import create_client

# Configuracao visual da pagina
st.set_page_config(page_title="RDO Digital - Minerva", layout="wide", page_icon="🏗️")

# Conexao com o Supabase
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()


def carregar_dados(nome_tabela):
    try:
        res = supabase.table(nome_tabela).select("*").order("id").execute()
        return pd.DataFrame(res.data)
    except Exception:
        return pd.DataFrame()


def salvar_dados(dados_dict, nome_tabela):
    supabase.table(nome_tabela).insert(dados_dict).execute()


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
        salvar_dados({
            "data": data_rdo.strftime("%d/%m/%Y"),
            "clima_manha": clima_m,
            "clima_tarde": clima_t,
            "condicao": condicao,
            "horas_paradas": horas_chuva,
            "terceiros": ", ".join(empresas),
            "obs_visitas": obs_visitas,
            "atividades": atividades
        }, "rdo_diario")
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
            "Impermeabilização", "Gesso", "Drywall", "Carpintaria", "Pintura", "Armador"
        ])
        status_serv = st.selectbox("Status", ["Iniciado", "Em Andamento", "Concluído"])

    if st.button("Registrar Alocação de Equipe"):
        salvar_dados({
            "data": datetime.today().strftime("%d/%m/%Y"),
            "colaborador": colab,
            "empresa": emp_colab,
            "pavimento": pav,
            "unidade": apto,
            "servico": serv,
            "status": status_serv
        }, "alocacao_equipes")
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
        salvar_dados({
            "data": datetime.today().strftime("%d/%m/%Y"),
            "concreteira": concreteira,
            "nf": nf,
            "peca": peca,
            "fck": int(fck),
            "volume_m3": float(vol_m3),
            "slump_cm": int(slump),
            "status": status_conc
        }, "concretagem")
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
        salvar_dados({
            "data_abertura": datetime.today().strftime("%d/%m/%Y"),
            "local": local_issue,
            "disciplina": disc_issue,
            "descricao": desc_issue,
            "responsavel": resp_issue,
            "prazo": prazo_issue.strftime("%d/%m/%Y"),
            "status": "Aberto"
        }, "issues")
        st.warning(f"📌 RNC aberta e atribuída para: {resp_issue}")

# ==========================================
# ABA 5: PAINEL DO COORDENADOR (VISUALIZAÇÃO)
# ==========================================
with aba5:
    st.subheader("📊 Visão Gerencial em Tempo Real")
    st.info("Dados sincronizados na nuvem. Dê dois cliques em qualquer célula para editar e clique em Salvar.")

    tab_v1, tab_v2, tab_v3, tab_v4 = st.tabs(["Histórico RDO", "Mapa de Equipes", "Concretagem", "RNCs Abertas"])

    def exibir_tabela_editavel(nome_tabela, chave_unica):
        df_atual = carregar_dados(nome_tabela)
        if not df_atual.empty:
            df_editado = st.data_editor(df_atual, use_container_width=True, disabled=["id"], key=chave_unica)
            if st.button(f"💾 Salvar alterações em {nome_tabela}", key=f"btn_{chave_unica}"):
                for _, row in df_editado.iterrows():
                    dados_linha = row.drop("id").to_dict()
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
        ["rdo_diario", "alocacao_equipes", "concretagem", "issues"]
    )
    df_exclusao = carregar_dados(aba_escolhida)

    if not df_exclusao.empty:
        opcoes = [f"ID {row['id']} | {row.iloc[1]} - {row.iloc[2]}" for _, row in df_exclusao.iterrows()]
        selecionado = st.selectbox("Selecione o registro para apagar:", opcoes)

        if st.button("Excluir Registro Selecionado", type="primary"):
            id_registro = int(selecionado.split(" ")[1])
            supabase.table(aba_escolhida).delete().eq("id", id_registro).execute()
            st.success("Registro excluído da nuvem!")
            st.rerun()
    else:
        st.info("Nenhum registro cadastrado nesta categoria.")

    # --- BOTÃO PARA BAIXAR PLANILHA EXCEL COMPLETA ---
    # --- BOTÃO PARA BAIXAR PLANILHA EXCEL COMPLETA ---
    st.divider()
    output_excel = io.BytesIO()
    with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
        tem_dados = False
        for tabela in ["rdo_diario", "alocacao_equipes", "concretagem", "issues"]:
            df_temp = carregar_dados(tabela)
            if not df_temp.empty:
                df_temp.to_excel(writer, sheet_name=tabela, index=False)
                tem_dados = True
        if not tem_dados:
            pd.DataFrame({"Aviso": ["Nenhum registro cadastrado no banco de dados ainda."]}).to_excel(
                writer, sheet_name="Resumo", index=False
            )

    st.download_button(
        label="📥 Baixar Planilha Completa da Obra (Excel)",
        data=output_excel.getvalue(),
        file_name="Relatorio_Geral_Jardins_de_Nazare.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )