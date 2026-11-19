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
st.title("🏗️ RDO Digital/Gestão de Campo")
st.markdown("Obra: Jardins de Nazaré | Construtora Minerva | Engenharia 4.0 - 👷🏽‍♀️Sara Elienai")
st.divider()

# --- MENU DE ABAS ---
aba1, aba2, aba3, aba4, aba5 = st.tabs((
    "📋 RDO/Clima",
    "👷 Equipes/Apartamentos",
    "🚛 Concretagem",
    "📌 RNC (Qualidade)",
    "📊 Painel do Coordenador"
))

# ==========================================
# ABA 1: RDO DIÁRIO E CLIMA REAL + PDF/FOTOS
# ==========================================
with aba1:
    st.subheader("Registro Diário de Obra")
    col1, col2, col3 = st.columns(3)
    with col1:
        data_rdo = st.date_input("Data", datetime.today())
    with col2:
        clima_m = st.selectbox("Clima Manhã (Real)", ("Bom / Sol", "Nublado", "Chuva Fraca", "Chuva Forte"))
    with col3:
        clima_t = st.selectbox("Clima Tarde (Real)", ("Bom / Sol", "Nublado", "Chuva Fraca", "Chuva Forte"))

    condicao = st.radio(
        "Condição de Trabalho no Canteiro",
        ("Praticável", "Parcialmente Impraticável", "Totalmente Impraticável"),
        horizontal=True
    )

    horas_chuva = 0.0
    if "Chuva" in clima_m or "Chuva" in clima_t:
        horas_chuva = st.number_input("Quantas horas a obra ficou parada por chuva?", min_value=0.0, max_value=12.0, step=0.5)

    empresas = st.multiselect("Empresas / Visitas Técnicas Presentes", (
        "Equipe Própria Minerva",
        "Cerqueira (Empreiteira)",
        "Saint-Gobain (Monocapa)",
        "Fiscalização / Prefeitura",
        "Equipe GWF",
        "Equipe FG",
        "Outros Fornecedores"
    ))
    obs_visitas = st.text_input("Detalhes das visitas (Ex: Técnico da Saint-Gobain validou fachada norte)")
    atividades = st.text_area("Resumo das Atividades Executadas Hoje")

    if st.button("Salvar RDO do Dia", type="primary"):
        ok = salvar_dados({
            "data": data_rdo.strftime("%d/%m/%Y"),
            "clima_manha": clima_m,
            "clima_tarde": clima_t,
            "condicao": condicao,
            "horas_paradas": float(horas_chuva),
            "terceiros": ", ".join(empresas),
            "obs_visitas": obs_visitas,
            "atividades": atividades
        }, "rdo_diario")
        if ok:
            st.success("✅ RDO salvo na nuvem com sucesso!")

    # --- GERADOR DE PDF COM FOTOS NA ABA 1 ---
    st.divider()
    st.subheader("📄 Gerar Relatório Diário em PDF (Com Fotos)")

    fotos_galeria = st.file_uploader(
    "Anexar fotos do serviço executado (JPG ou PNG):",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
    )
    foto_camera = st.camera_input("Ou tirar foto na hora pela câmera")

    fotos_enviadas = list(fotos_galeria) if fotos_galeria else []
    if foto_camera is not None:
     fotos_enviadas.append(foto_camera)

    if st.button("Preparar PDF do Último RDO"):
        df_rdo_atual = carregar_dados("rdo_diario")
        pdf_pronto = criar_pdf_rdo(df_rdo_atual, fotos_enviadas)

        st.success("PDF gerado com sucesso! Clique abaixo para baixar.")
        st.download_button(
            label="📥 Baixar Relatório RDO em PDF",
            data=pdf_pronto,
            file_name=f"RDO_Minerva_Jardins_{datetime.today().strftime('%Y%m%d')}.pdf",
            mime="application/pdf"
        )
        # ==========================================
# ABA 2: ALOCAÇÃO DE EQUIPES POR APARTAMENTO
# ==========================================
with aba2:
    st.subheader("Rastreabilidade de Equipes por Pavimento/Unidade")
    c1, c2, c3 = st.columns(3)
    with c1:
        colab = st.text_input("Nome do Colaborador ou Líder de Equipe")
        emp_colab = st.selectbox("Empresa", ("Construtora Minerva", "Cerqueira", "Saint-Gobain-Monocapa", "DWG Hidraulica", "FG Elétrica", "Outra"))
    with c2:
        pav = st.selectbox("Pavimento", (
            "Subsolo", "Térreo", "1º Pavimento", "2º Pavimento", "3º Pavimento",
            "4º Pavimento", "5º Pavimento", "6º Pavimento", "7º Pavimento",
            "8º Pavimento", "9º Pavimento", "Cobertura", "Fachada", "Muro"
        ))
        apto = st.text_input("Apartamento ou Local (Ex: Apto 102, Hall)")
    with c3:
        serv = st.selectbox("Serviço Executado", (
            "Alvenaria", "Monocapa", "Contrapiso", "Hidráulica", "Elétrica",
            "Impermeabilização", "Gesso", "Drywall", "Carpintaria", "Pintura", "Armador"
        ))
        status_serv = st.selectbox("Status", ("Iniciado", "Em Andamento", "Concluído"))

    if st.button("Registrar Alocação de Equipe"):
        ok = salvar_dados({
            "data": datetime.today().strftime("%d/%m/%Y"),
            "colaborador": colab,
            "empresa": emp_colab,
            "pavimento": pav,
            "unidade": apto,
            "servico": serv,
            "status": status_serv
        }, "alocacao_equipes")
        if ok:
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
        fck = st.selectbox("FCK de Projeto (MPa)", (20, 25, 30, 35, 40))
    with cc3:
        vol_m3 = st.number_input("Volume (m³)", min_value=0.5, step=0.5)
        slump = st.number_input("Slump Obtido na Obra (cm)", min_value=1, max_value=30, value=12)

    status_conc = st.radio("Status do Recebimento", ("Aprovado", "Aprovado com Aditivo", "Recusado"), horizontal=True)

    if st.button("Salvar Caminhão de Concreto"):
        ok = salvar_dados({
            "data": datetime.today().strftime("%d/%m/%Y"),
            "concreteira": concreteira,
            "nf": nf,
            "peca": peca,
            "fck": int(fck),
            "volume_m3": float(vol_m3),
            "slump_cm": int(slump),
            "status": status_conc
        }, "concretagem")
        if ok:
            st.success(f"✅ Caminhão NF {nf} ({vol_m3} m³) registrado!")

# ==========================================
# ABA 4: RNC (CONTROLE DE QUALIDADE)
# ==========================================
with aba4:
    st.subheader("Registro de Não Conformidade (RNC)")
    ci1, ci2 = st.columns(2)
    with ci1:
        local_issue = st.text_input("Local da Não Conformidade (Ex: Pilar P14 - Térreo)")
        disc_issue = st.selectbox("Disciplina", (
            "Estrutura", "Alvenaria", "Monocapa / Fachada", "Instalações",
            "Drywall", "Carpintaria", "Contrapiso", "Hidraulica", "Elétrica", "Segurança do Trabalho"
        ))
    with ci2:
        resp_issue = st.selectbox("Responsável pela Correção", ("Mestre de Obras", "Cerqueira", "Saint-Gobain", "Equipe Minerva"))
        prazo_issue = st.date_input("Prazo Limite para Correção")

    desc_issue = st.text_area("Descrição detalhada do problema")

    if st.button("Abrir RNC de Qualidade"):
        ok = salvar_dados({
            "data_abertura": datetime.today().strftime("%d/%m/%Y"),
            "local": local_issue,
            "disciplina": disc_issue,
            "descricao": desc_issue,
            "responsavel": resp_issue,
            "prazo": prazo_issue.strftime("%d/%m/%Y"),
            "status": "Aberto"
        }, "issues")
        if ok:
            st.warning(f"📌 RNC aberta e atribuída para: {resp_issue}")

# ==========================================
# ABA 5: PAINEL DO COORDENADOR (VISUALIZAÇÃO)
# ==========================================
with aba5:
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
