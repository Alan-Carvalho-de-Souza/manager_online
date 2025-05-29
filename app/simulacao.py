# Arquivo: app/simulacao.py (versão com componentes nativos)
import streamlit as st
import pandas as pd
import random
import time
from utils.io import salvar_resultado
import base64
from io import BytesIO
from PIL import Image
from collections import Counter

def configurar_streamlit():
    """Configurações iniciais do Streamlit"""
    if 'animacao_ativa' not in st.session_state:
        st.session_state.animacao_ativa = False
    if 'frame_atual' not in st.session_state:
        st.session_state.frame_atual = 0

def base64_to_image(base64_string):
    """Converte base64 para objeto de imagem"""
    try:
        img_data = base64.b64decode(base64_string)
        return Image.open(BytesIO(img_data))
    except:
        return None

def exibir_placar_nativo(container, clube1, clube2, gols1, gols2, minutos, destaque=None):
    """
    Exibe o placar usando apenas componentes nativos do Streamlit
    """
    with container.container():
        # Cabeçalho com tempo e destaque
        if destaque:
            st.info(f"⏱️ {minutos}' - {destaque}")
        else:
            st.info(f"⏱️ Tempo de jogo: {minutos}'")
        
        # Criar layout em colunas para o placar
        col1, col2, col3, col4, col5 = st.columns([1, 2, 1, 2, 1])
        
        # Time 1 - Logo
        with col1:
            if clube1.get('logo_base64'):
                img = base64_to_image(clube1['logo_base64'])
                if img:
                    st.image(img, width=80)
            else:
                st.write("🏟️")
        
        # Time 1 - Nome e Placar
        with col2:
            st.markdown(f"### {clube1['nome']}")
            st.markdown(f"# {gols1}")
        
        # Separador
        with col3:
            st.markdown("")
            st.markdown("# ×")
        
        # Time 2 - Nome e Placar
        with col4:
            st.markdown(f"### {clube2['nome']}")
            st.markdown(f"# {gols2}")
        
        # Time 2 - Logo
        with col5:
            if clube2.get('logo_base64'):
                img = base64_to_image(clube2['logo_base64'])
                if img:
                    st.image(img, width=80)
            else:
                st.write("🏟️")

def exibir_placar_metrica(container, clube1, clube2, gols1, gols2, minutos, destaque=None):
    """
    Versão alternativa usando st.metric
    """
    with container.container():
        # Tempo e destaque
        tempo_col, destaque_col = st.columns([1, 2])
        with tempo_col:
            st.metric("Tempo", f"{minutos}'")
        with destaque_col:
            if destaque:
                if "GOL" in destaque:
                    st.success(destaque)
                elif "INTERVALO" in destaque:
                    st.warning(destaque)
                elif "FIM" in destaque:
                    st.error(destaque)
        
        # Placar
        st.markdown("---")
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col1:
            if clube1.get('logo_base64'):
                img = base64_to_image(clube1['logo_base64'])
                if img:
                    st.image(img, width=60)
            st.metric(label=clube1['nome'], value=gols1, delta=None)
        
        with col2:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown("### VS")
        
        with col3:
            if clube2.get('logo_base64'):
                img = base64_to_image(clube2['logo_base64'])
                if img:
                    st.image(img, width=60)
            st.metric(label=clube2['nome'], value=gols2, delta=None)

def animar_gol(container, clube1, clube2, gols1, gols2, minutos):
    """Animação de gol usando componentes nativos"""
    for i in range(3):
        container.empty()
        if i % 2 == 0:
            exibir_placar_nativo(container, clube1, clube2, gols1, gols2, minutos, "⚽ GOOOOOL! 🎯")
        else:
            exibir_placar_nativo(container, clube1, clube2, gols1, gols2, minutos)
        time.sleep(0.4)

def animar_intervalo(container, clube1, clube2, gols1, gols2, minutos):
    """Animação para o intervalo"""
    container.empty()
    exibir_placar_nativo(container, clube1, clube2, gols1, gols2, minutos, "🔄 INTERVALO")
    time.sleep(1.5)

def animar_fim_jogo(container, clube1, clube2, gols1, gols2, minutos):
    """Animação para o fim do jogo"""
    container.empty()
    exibir_placar_nativo(container, clube1, clube2, gols1, gols2, minutos, "🏁 FIM DE JOGO!")
    time.sleep(1.5)

def validar_dados_clube(clube):
    """Valida os dados do clube"""
    campos_obrigatorios = ['nome', 'forca_geral', 'jogadores']
    for campo in campos_obrigatorios:
        if campo not in clube:
            raise ValueError(f"Campo '{campo}' não encontrado no clube")
    
    if not clube['jogadores']:
        raise ValueError(f"O clube {clube['nome']} não tem jogadores")
    
    for jogador in clube['jogadores']:
        if 'habilidade' not in jogador or 'nome' not in jogador:
            raise ValueError(f"Jogador sem dados completos em {clube['nome']}")

def calcular_media_habilidade(jogadores):
    """Calcula a média de habilidade dos jogadores"""
    if not jogadores:
        return 50
    return sum(j.get('habilidade', 50) for j in jogadores) / len(jogadores)

def simular_partida(clube1, clube2):
    """
    Simula uma partida usando apenas componentes nativos do Streamlit
    """
    try:
        # Validação
        validar_dados_clube(clube1)
        validar_dados_clube(clube2)
    except ValueError as e:
        st.error(f"❌ Erro nos dados: {e}")
        return 0, 0
    
    # Configuração inicial
    configurar_streamlit()
    
    # Título da partida
    st.title("⚽ Simulação de Partida")
    st.markdown(f"### {clube1['nome']} vs {clube2['nome']}")
    
    # Separador
    st.markdown("---")
    
    # Container principal do placar
    placar_container = st.empty()
    
    # Área de informações
    st.markdown("---")
    
    # Layout em duas colunas: eventos e estatísticas
    col_eventos, col_stats = st.columns([2, 1])
    
    with col_eventos:
        st.subheader("📝 Eventos da Partida")
        eventos_container = st.container()
    
    with col_stats:
        st.subheader("📊 Estatísticas")
        stats_container = st.container()
        progresso = stats_container.progress(0)
        tempo_texto = stats_container.empty()
    
    # Inicialização
    gols1 = gols2 = 0
    minutos = 0
    eventos = []
    marcadores_gols = []
    
    # Estatísticas detalhadas
    finalizacoes1 = finalizacoes2 = 0
    finalizacoes_gol1 = finalizacoes_gol2 = 0
    defesas1 = defesas2 = 0
    posse_bola1 = posse_bola2 = 0
    faltas1 = faltas2 = 0
    escanteios1 = escanteios2 = 0
    cartoes_amarelos1 = cartoes_amarelos2 = 0
    
    # Exibir placar inicial
    exibir_placar_nativo(placar_container, clube1, clube2, 0, 0, 0)
    
    # Fatores do jogo
    fator_casa = random.uniform(1.05, 1.15)
    fator_dia_clube1 = random.uniform(0.85, 1.15)
    fator_dia_clube2 = random.uniform(0.85, 1.15)
    
    forca_efetiva_clube1 = clube1['forca_geral'] * fator_casa * fator_dia_clube1
    forca_efetiva_clube2 = clube2['forca_geral'] * fator_dia_clube2
    
    # Informações pré-jogo
    with eventos_container:
        info_container = st.container()
        with info_container:
            if fator_dia_clube1 > 1.1:
                st.success(f"🔥 {clube1['nome']} está em um dia inspirado!")
            if fator_dia_clube2 > 1.1:
                st.success(f"🔥 {clube2['nome']} está em um dia inspirado!")
            st.info("📢 Começa a partida!")
    
    # Placeholder para eventos
    eventos_placeholder = eventos_container.empty()
    
    # Simulação
    for periodo in range(2):
        tempo_inicial = 0 if periodo == 0 else 45
        tempo_final = 45 if periodo == 0 else 90
        
        num_eventos = random.randint(8, 12)
        
        for _ in range(num_eventos):
            # Avança o tempo
            if minutos < tempo_final:
                minutos = min(minutos + random.randint(3, 8), tempo_final)
            
            # Atualiza progresso
            progresso_percentual = int((minutos / 90) * 100)
            progresso.progress(progresso_percentual)
            tempo_texto.markdown(f"**Tempo: {minutos} minutos**")
            
            # Atualiza placar
            exibir_placar_nativo(placar_container, clube1, clube2, gols1, gols2, minutos)
            
            # Determina time atacante baseado na força
            soma_forcas = forca_efetiva_clube1 + forca_efetiva_clube2
            prob_clube1 = forca_efetiva_clube1 / soma_forcas
            
            # Ajuste por diferença de gols (time perdendo ataca mais)
            diferenca_gols = gols1 - gols2
            if diferenca_gols >= 2:
                prob_clube1 *= 0.8
            elif diferenca_gols <= -2:
                prob_clube1 *= 1.2
            prob_clube1 = max(0.3, min(0.7, prob_clube1))
            
            time_atacante = 1 if random.random() < prob_clube1 else 2
            
            # Chance de finalização (20%)
            if random.random() < 0.20:
                if time_atacante == 1:
                    finalizacoes1 += 1
                    
                    # Chance da finalização ir no gol (60%)
                    if random.random() < 0.60:
                        finalizacoes_gol1 += 1
                        
                        # Chance de gol (40% das finalizações no gol)
                        if random.random() < 0.40:
                            gols1 += 1
                            jogadores = [j for j in clube1['jogadores'] if j.get('posicao') != 'Goleiro']
                            if jogadores:
                                marcador = random.choice(jogadores)
                                evento = f"⚽ {minutos}' - GOL! {marcador['nome']} marca para o {clube1['nome']}!"
                                marcadores_gols.append((marcador['nome'], minutos, clube1['nome']))
                            else:
                                evento = f"⚽ {minutos}' - GOL do {clube1['nome']}!"
                            eventos.append(evento)
                            animar_gol(placar_container, clube1, clube2, gols1, gols2, minutos)
                        else:
                            # Defesa do goleiro
                            defesas2 += 1
                            goleiro = next((j for j in clube2['jogadores'] if j.get('posicao') == 'Goleiro'), None)
                            if goleiro:
                                evento = f"🧤 {minutos}' - Grande defesa de {goleiro['nome']} ({clube2['nome']})!"
                            else:
                                evento = f"🧤 {minutos}' - Defesa do goleiro do {clube2['nome']}!"
                            eventos.append(evento)
                    else:
                        # Finalização para fora
                        evento = f"😮 {minutos}' - {clube1['nome']} finaliza para fora!"
                        eventos.append(evento)
                else:
                    finalizacoes2 += 1
                    
                    # Chance da finalização ir no gol (60%)
                    if random.random() < 0.60:
                        finalizacoes_gol2 += 1
                        
                        # Chance de gol (40% das finalizações no gol)
                        if random.random() < 0.40:
                            gols2 += 1
                            jogadores = [j for j in clube2['jogadores'] if j.get('posicao') != 'Goleiro']
                            if jogadores:
                                marcador = random.choice(jogadores)
                                evento = f"⚽ {minutos}' - GOL! {marcador['nome']} marca para o {clube2['nome']}!"
                                marcadores_gols.append((marcador['nome'], minutos, clube2['nome']))
                            else:
                                evento = f"⚽ {minutos}' - GOL do {clube2['nome']}!"
                            eventos.append(evento)
                            animar_gol(placar_container, clube1, clube2, gols1, gols2, minutos)
                        else:
                            # Defesa do goleiro
                            defesas1 += 1
                            goleiro = next((j for j in clube1['jogadores'] if j.get('posicao') == 'Goleiro'), None)
                            if goleiro:
                                evento = f"🧤 {minutos}' - Grande defesa de {goleiro['nome']} ({clube1['nome']})!"
                            else:
                                evento = f"🧤 {minutos}' - Defesa do goleiro do {clube1['nome']}!"
                            eventos.append(evento)
                    else:
                        # Finalização para fora
                        evento = f"😮 {minutos}' - {clube2['nome']} finaliza para fora!"
                        eventos.append(evento)
                        
            # Outros eventos (10% de chance)
            elif random.random() < 0.10:
                tipo_evento = random.choice(['falta', 'escanteio', 'cartao'])
                
                if tipo_evento == 'falta':
                    if random.random() < prob_clube1:
                        faltas1 += 1
                        evento = f"⚠️ {minutos}' - Falta cometida por {clube1['nome']}"
                    else:
                        faltas2 += 1
                        evento = f"⚠️ {minutos}' - Falta cometida por {clube2['nome']}"
                    eventos.append(evento)
                    
                elif tipo_evento == 'escanteio':
                    if random.random() < prob_clube1:
                        escanteios1 += 1
                        evento = f"🚩 {minutos}' - Escanteio para {clube1['nome']}"
                    else:
                        escanteios2 += 1
                        evento = f"🚩 {minutos}' - Escanteio para {clube2['nome']}"
                    eventos.append(evento)
                    
                elif tipo_evento == 'cartao' and random.random() < 0.3:  # Cartões são mais raros
                    if random.random() < prob_clube1:
                        cartoes_amarelos1 += 1
                        jogador = random.choice(clube1['jogadores'])
                        evento = f"🟨 {minutos}' - Cartão amarelo para {jogador['nome']} ({clube1['nome']})"
                    else:
                        cartoes_amarelos2 += 1
                        jogador = random.choice(clube2['jogadores'])
                        evento = f"🟨 {minutos}' - Cartão amarelo para {jogador['nome']} ({clube2['nome']})"
                    eventos.append(evento)
            
            # Atualiza lista de eventos (mostra últimos 5)
            with eventos_placeholder.container():
                for evento in eventos[-5:]:
                    if "GOL" in evento:
                        st.success(evento)
                    elif "defesa" in evento.lower():
                        st.info(evento)
                    elif "Cartão" in evento:
                        st.warning(evento)
                    elif "Falta" in evento:
                        st.warning(evento)
                    elif "Escanteio" in evento:
                        st.info(evento)
                    elif "finaliza" in evento:
                        st.warning(evento)
                    else:
                        st.info(evento)
            
            # Contabiliza posse de bola
            if time_atacante == 1:
                posse_bola1 += 1
            else:
                posse_bola2 += 1
            
            # Pausa entre eventos
            time.sleep(0.3)
        
        # Intervalo
        if periodo == 0:
            evento_intervalo = f"⏱️ 45' - Fim do 1º tempo: {clube1['nome']} {gols1} x {gols2} {clube2['nome']}"
            eventos.append(evento_intervalo)
            
            animar_intervalo(placar_container, clube1, clube2, gols1, gols2, 45)
            
            with eventos_placeholder.container():
                st.warning(evento_intervalo)
            
            # Chance de motivação no intervalo
            if gols1 < gols2 and random.random() < 0.3:
                forca_efetiva_clube1 *= 1.1
                eventos.append(f"🗣️ {clube1['nome']} volta motivado do intervalo!")
            elif gols2 < gols1 and random.random() < 0.3:
                forca_efetiva_clube2 *= 1.1
                eventos.append(f"🗣️ {clube2['nome']} volta motivado do intervalo!")
    
    # Fim do jogo
    animar_fim_jogo(placar_container, clube1, clube2, gols1, gols2, 90)
    
    # Ajuste final de estatísticas para garantir realismo
    # Garante que cada time tenha pelo menos algumas finalizações
    if finalizacoes1 < 3:
        finalizacoes1 += random.randint(2, 4)
    if finalizacoes2 < 3:
        finalizacoes2 += random.randint(2, 4)
    
    # Ajusta finalizações no gol baseado no total
    if finalizacoes_gol1 < gols1:
        finalizacoes_gol1 = gols1 + random.randint(1, 3)
    if finalizacoes_gol2 < gols2:
        finalizacoes_gol2 = gols2 + random.randint(1, 3)
    
    # Garante que finalizações no gol não excedam total de finalizações
    finalizacoes_gol1 = min(finalizacoes_gol1, finalizacoes1)
    finalizacoes_gol2 = min(finalizacoes_gol2, finalizacoes2)
    
    # Resultado final
    st.markdown("---")
    st.success(f"🏁 **RESULTADO FINAL: {clube1['nome']} {gols1} x {gols2} {clube2['nome']}**")
    
    # Estatísticas finais em expander
    with st.expander("📊 Ver Estatísticas Detalhadas da Partida", expanded=False):
        # Resumo da partida
        st.subheader("📋 Resumo da Partida")
        
        # Determinar vencedor
        if gols1 > gols2:
            resultado_texto = f"🏆 Vitória do {clube1['nome']}"
            st.success(resultado_texto)
        elif gols2 > gols1:
            resultado_texto = f"🏆 Vitória do {clube2['nome']}"
            st.success(resultado_texto)
        else:
            resultado_texto = "🤝 Empate"
            st.info(resultado_texto)
        
        # Estatísticas rápidas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total de Gols", gols1 + gols2)
        with col2:
            st.metric("Total de Finalizações", finalizacoes1 + finalizacoes2)
        with col3:
            st.metric("Total de Defesas", defesas1 + defesas2)
        with col4:
            st.metric("Total de Faltas", faltas1 + faltas2)
        
        st.markdown("---")
        
        # Placar final
        st.subheader("🏆 Placar Final")
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col1:
            st.metric(clube1['nome'], gols1)
        with col2:
            st.markdown("### x")
        with col3:
            st.metric(clube2['nome'], gols2)
        
        # Marcadores
        if marcadores_gols:
            st.subheader("⚽ Marcadores de Gols")
            
            # Identificar artilheiro da partida
            todos_marcadores = [m[0] for m in marcadores_gols]
            contador_gols = Counter(todos_marcadores)
            artilheiro = contador_gols.most_common(1)[0] if contador_gols else None
            
            if artilheiro and artilheiro[1] > 1:
                st.info(f"🏅 Artilheiro da partida: {artilheiro[0]} ({artilheiro[1]} gols)")
            
            col1, col2 = st.columns(2)
            
            gols_time1 = [(j, m) for j, m, t in marcadores_gols if t == clube1['nome']]
            gols_time2 = [(j, m) for j, m, t in marcadores_gols if t == clube2['nome']]
            
            with col1:
                st.markdown(f"**{clube1['nome']}**")
                if gols_time1:
                    for jogador, minuto in gols_time1:
                        st.write(f"⚽ {jogador} ({minuto}')")
                else:
                    st.write("*Sem gols*")
            
            with col2:
                st.markdown(f"**{clube2['nome']}**")
                if gols_time2:
                    for jogador, minuto in gols_time2:
                        st.write(f"⚽ {jogador} ({minuto}')")
                else:
                    st.write("*Sem gols*")
        
        # Estatísticas gerais
        st.subheader("📈 Estatísticas Gerais")
        
        # Posse de bola baseada em dados reais da partida
        total_posse = posse_bola1 + posse_bola2
        if total_posse > 0:
            posse_time1 = round((posse_bola1 / total_posse) * 100)
            posse_time2 = round((posse_bola2 / total_posse) * 100)
        else:
            # Fallback para cálculo baseado em força
            posse_time1 = round((forca_efetiva_clube1 / (forca_efetiva_clube1 + forca_efetiva_clube2)) * 100)
            posse_time2 = 100 - posse_time1
        
        # Criar DataFrame com todas as estatísticas
        stats_df = pd.DataFrame({
            'Estatística': [
                'Posse de Bola (%)', 
                'Gols', 
                'Finalizações',
                'Finalizações no Gol',
                'Defesas do Goleiro',
                'Faltas',
                'Escanteios',
                'Cartões Amarelos'
            ],
            clube1['nome']: [
                posse_time1, 
                gols1, 
                finalizacoes1,
                finalizacoes_gol1,
                defesas1,
                faltas1,
                escanteios1,
                cartoes_amarelos1
            ],
            clube2['nome']: [
                posse_time2, 
                gols2, 
                finalizacoes2,
                finalizacoes_gol2,
                defesas2,
                faltas2,
                escanteios2,
                cartoes_amarelos2
            ]
        })
        
        st.dataframe(stats_df, hide_index=True, use_container_width=True)
        
        # Métricas adicionais
        st.subheader("📊 Métricas de Desempenho")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**{clube1['nome']}**")
            # Eficiência de finalização
            if finalizacoes1 > 0:
                eficiencia1 = round((gols1 / finalizacoes1) * 100, 1)
                st.metric("Eficiência de Finalização", f"{eficiencia1}%")
            else:
                st.metric("Eficiência de Finalização", "0%")
            
            # Precisão de finalização
            if finalizacoes1 > 0:
                precisao1 = round((finalizacoes_gol1 / finalizacoes1) * 100, 1)
                st.metric("Precisão de Finalização", f"{precisao1}%")
            else:
                st.metric("Precisão de Finalização", "0%")
        
        with col2:
            st.markdown(f"**{clube2['nome']}**")
            # Eficiência de finalização
            if finalizacoes2 > 0:
                eficiencia2 = round((gols2 / finalizacoes2) * 100, 1)
                st.metric("Eficiência de Finalização", f"{eficiencia2}%")
            else:
                st.metric("Eficiência de Finalização", "0%")
            
            # Precisão de finalização
            if finalizacoes2 > 0:
                precisao2 = round((finalizacoes_gol2 / finalizacoes2) * 100, 1)
                st.metric("Precisão de Finalização", f"{precisao2}%")
            else:
                st.metric("Precisão de Finalização", "0%")
        
        # Visualização gráfica das estatísticas
        st.subheader("📊 Comparativo Visual")
        
        # Gráfico de barras comparativo
        chart_data = pd.DataFrame({
            clube1['nome']: [finalizacoes1, finalizacoes_gol1, defesas1, faltas1, escanteios1],
            clube2['nome']: [finalizacoes2, finalizacoes_gol2, defesas2, faltas2, escanteios2]
        }, index=['Finalizações', 'No Gol', 'Defesas', 'Faltas', 'Escanteios'])
        
        st.bar_chart(chart_data)
        
        # Todos os eventos
        st.subheader("📝 Todos os Eventos da Partida")
        for i, evento in enumerate(eventos):
            if "GOL" in evento:
                st.success(f"{i+1}. {evento}")
            elif "defesa" in evento.lower():
                st.info(f"{i+1}. {evento}")
            elif "Cartão" in evento:
                st.warning(f"{i+1}. {evento}")
            elif "Falta" in evento:
                st.warning(f"{i+1}. {evento}")
            elif "Escanteio" in evento:
                st.info(f"{i+1}. {evento}")
            elif "finaliza" in evento:
                st.warning(f"{i+1}. {evento}")
            elif "Fim do" in evento or "volta motivado" in evento:
                st.info(f"{i+1}. {evento}")
            else:
                st.write(f"{i+1}. {evento}")
    
        # Melhores momentos
        st.subheader("🌟 Melhores Momentos")
        
        # Filtrar apenas eventos importantes
        eventos_importantes = [e for e in eventos if any(palavra in e for palavra in ["GOL", "defesa", "Cartão"])]
        
        if eventos_importantes:
            # Mostrar últimos 10 momentos importantes
            for evento in eventos_importantes[-10:]:
                if "GOL" in evento:
                    st.success(f"⭐ {evento}")
                elif "defesa" in evento.lower():
                    st.info(f"⭐ {evento}")
                elif "Cartão" in evento:
                    st.warning(f"⭐ {evento}")
        else:
            st.info("Partida sem grandes emoções")
    
    # Salvar resultado
    try:
        salvar_resultado(clube1, clube2, gols1, gols2, marcadores_gols)
        st.info("💾 Resultado salvo no histórico!")
    except Exception as e:
        st.warning(f"⚠️ Não foi possível salvar o resultado: {e}")
    
    return gols1, gols2