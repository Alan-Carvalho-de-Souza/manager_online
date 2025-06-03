# Arquivo: app/simulacao_otimizada_integrada.py
import random
import numpy as np
import pandas as pd
import streamlit as st
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import time

# Importar suas funções existentes
from utils.io import carregar_clubes, carregar_jogadores, salvar_resultado

# ===== MANTER FUNÇÃO ORIGINAL PARA COMPATIBILIDADE =====
def simular_partida_automatica(clube1, clube2):
    """
    Função original mantida para compatibilidade total.
    Esta é a mesma função que você tinha antes.
    """
    # Calcular habilidade média dos times
    habilidade1 = sum(j['habilidade'] for j in clube1['jogadores']) / len(clube1['jogadores'])
    habilidade2 = sum(j['habilidade'] for j in clube2['jogadores']) / len(clube2['jogadores'])
    
    # Adicionar pequeno bônus para o mandante (fator casa)
    habilidade1 += 2
    
    # Calcular probabilidades baseadas nas habilidades
    total_habilidade = habilidade1 + habilidade2
    prob1 = habilidade1 / total_habilidade
    
    # Simular número de gols para cada time
    gols1 = 0
    gols2 = 0
    
    # Simular aproximadamente 5-10 chances de gol por jogo
    num_chances = random.randint(5, 10)
    
    for _ in range(num_chances):
        # Decidir qual time tem a chance
        if random.random() < prob1:
            # Chance para o mandante
            if random.random() < 0.45:  # 45% de chance de converter em gol
                gols1 += 1
        else:
            # Chance para o visitante
            if random.random() < 0.30:  # 30% de chance (visitante tem menos chance)
                gols2 += 1
    
    # Garantir pelo menos alguma variação nos resultados
    if random.random() < 0.20:  # 20% chance de gol extra aleatório
        if random.random() < 0.5:
            gols1 += 1
        else:
            gols2 += 1
    
    # Selecionar jogadores que marcaram e criar marcadores no formato correto
    artilheiros1 = []
    artilheiros2 = []
    marcadores_formatados = []  # Formato: Nome:Minuto:Time;Nome:Minuto:Time
    
    # Para o time 1
    for gol_num in range(gols1):
        # Dar maior probabilidade para atacantes e meio-campistas
        jogadores_peso = []
        for jogador in clube1['jogadores']:
            # Reconhecer abreviações da base CSV
            posicao = jogador.get('posicao', 'DEF').upper().strip()
            
            if posicao == 'ATA':  # Atacante
                peso = 3  # Atacantes têm 3x mais chance
            elif posicao == 'MEI':  # Meio-campista
                peso = 2  # Meio-campistas têm 2x mais chance
            elif posicao == 'DEF':  # Defensor
                peso = 1  # Defensores têm chance normal
            else:
                # Fallback para posições não reconhecidas
                peso = 1
            
            for _ in range(peso):
                jogadores_peso.append(jogador)
        
        if jogadores_peso:
            jogador_gol = random.choice(jogadores_peso)
            artilheiros1.append(f"{jogador_gol['nome']} ({clube1['nome']})")
            
            # Simular minuto do gol
            minuto = random.randint(1, 90)
            # Formato correto: Nome:Minuto:Time
            marcadores_formatados.append(f"{jogador_gol['nome']}:{minuto}:{clube1['nome']}")
    
    # Para o time 2
    for gol_num in range(gols2):
        jogadores_peso = []
        for jogador in clube2['jogadores']:
            # Reconhecer abreviações da base CSV
            posicao = jogador.get('posicao', 'DEF').upper().strip()
            
            if posicao == 'ATA':  # Atacante
                peso = 3
            elif posicao == 'MEI':  # Meio-campista
                peso = 2
            elif posicao == 'DEF':  # Defensor
                peso = 1
            else:
                # Fallback para posições não reconhecidas
                peso = 1
            
            for _ in range(peso):
                jogadores_peso.append(jogador)
        
        if jogadores_peso:
            jogador_gol = random.choice(jogadores_peso)
            artilheiros2.append(f"{jogador_gol['nome']} ({clube2['nome']})")
            
            # Simular minuto do gol
            minuto = random.randint(1, 90)
            # Formato correto: Nome:Minuto:Time
            marcadores_formatados.append(f"{jogador_gol['nome']}:{minuto}:{clube2['nome']}")
    
    # Determinar vencedor
    if gols1 > gols2:
        vencedor = clube1['nome']
    elif gols2 > gols1:
        vencedor = clube2['nome']
    else:
        vencedor = "Empate"
    
    # Juntar marcadores com ponto e vírgula (formato esperado pelo sistema)
    marcadores_gols_formatados = ';'.join(marcadores_formatados)
    
    # Criar resumo dos marcadores para exibição
    marcadores_resumo = f"{clube1['nome']} {gols1} x {gols2} {clube2['nome']}"
    
    return {
        'time_casa': clube1['nome'],
        'time_visitante': clube2['nome'],
        'gols_casa': gols1,
        'gols_visitante': gols2,
        'vencedor': vencedor,
        'artilheiros': artilheiros1 + artilheiros2,
        'marcadores_gols': marcadores_gols_formatados,  # Formato correto para CSV
        'marcadores_resumo': marcadores_resumo,  # Para exibição
        'data': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def calcular_estatisticas_time(jogadores):
    """
    Função original mantida para compatibilidade.
    Calcula estatísticas agregadas de um time.
    """
    if not jogadores:
        return {
            'habilidade_media': 0,
            'total_jogadores': 0,
            'melhor_jogador': None
        }
    
    habilidades = [j['habilidade'] for j in jogadores]
    
    return {
        'habilidade_media': sum(habilidades) / len(habilidades),
        'total_jogadores': len(jogadores),
        'melhor_jogador': max(jogadores, key=lambda x: x['habilidade']),
        'habilidade_maxima': max(habilidades),
        'habilidade_minima': min(habilidades)
    }

def debug_posicoes_jogadores(clube):
    """
    Função original mantida para compatibilidade.
    Função auxiliar para debugar as posições dos jogadores.
    """
    print(f"\n=== DEBUG POSIÇÕES - {clube['nome']} ===")
    for jogador in clube['jogadores']:
        posicao_original = jogador.get('posicao', 'N/A')
        posicao_processada = posicao_original.upper().strip() if posicao_original != 'N/A' else 'N/A'
        
        if posicao_processada == 'ATA':
            peso = 3
            tipo = "Atacante"
        elif posicao_processada == 'MEI':
            peso = 2
            tipo = "Meio-campista"
        elif posicao_processada == 'DEF':
            peso = 1
            tipo = "Defensor"
        else:
            peso = 1
            tipo = "Não reconhecida"
            
        print(f"  {jogador['nome']:20} | Posição: {posicao_original:5} | Processada: {posicao_processada:5} | Tipo: {tipo:15} | Peso: {peso}")

# ===== 1. FUNÇÃO DE CARREGAMENTO INTEGRADA =====
@st.cache_data
def carregar_dados_clubes():
    """
    Função que integra suas funções existentes do io.py
    com o sistema de cache otimizado do Streamlit
    """
    try:
        # Usar suas funções existentes
        clubes_dict = carregar_clubes()
        
        if not clubes_dict:
            st.error("Não foi possível carregar os clubes!")
            return {}
        
        # Carregar jogadores nos clubes
        carregar_jogadores(clubes=clubes_dict)
        
        # Converter formato para compatibilidade com otimizações
        # Mudando a chave de ID para nome do clube
        clubes_por_nome = {}
        
        for clube_id, dados_clube in clubes_dict.items():
            nome_clube = dados_clube['nome']
            
            # Manter a estrutura que suas simulações esperam
            clubes_por_nome[nome_clube] = {
                'id': clube_id,  # Manter ID original
                'nome': nome_clube,
                'forca_geral': dados_clube['forca_geral'],
                'logo_base64': dados_clube.get('logo_base64'),
                'jogadores': dados_clube['jogadores']  # Lista já populada pelo carregar_jogadores
            }
        
        return clubes_por_nome
        
    except Exception as e:
        st.error(f"Erro ao carregar dados dos clubes: {e}")
        return {}

# ===== 2. PRÉ-PROCESSAMENTO OTIMIZADO =====
@st.cache_data
def calcular_estatisticas_pre_processadas(_clubes_data):
    """
    Pre-processa estatísticas dos clubes para acelerar simulações
    Nota: _ no parâmetro para evitar hash do Streamlit
    """
    stats = {}
    
    for clube_nome, clube_data in _clubes_data.items():
        if clube_data['jogadores']:
            habilidades = [j['habilidade'] for j in clube_data['jogadores']]
            
            # Calcular pesos por posição uma única vez
            pesos_posicao = []
            for jogador in clube_data['jogadores']:
                posicao = jogador.get('posicao', 'DEF').upper().strip()
                if posicao == 'ATA':
                    peso = 3
                elif posicao == 'MEI':
                    peso = 2
                else:
                    peso = 1
                pesos_posicao.append(peso)
            
            stats[clube_nome] = {
                'habilidade_media': np.mean(habilidades),
                'forca_geral': clube_data.get('forca_geral', np.mean(habilidades)),
                'jogadores': clube_data['jogadores'],
                'pesos_posicao': pesos_posicao,
                'total_peso': sum(pesos_posicao),
                'logo_base64': clube_data.get('logo_base64'),
                'id_original': clube_data.get('id')  # Manter ID para compatibilidade
            }
    
    return stats

# ===== 3. SIMULAÇÃO OTIMIZADA INDIVIDUAL =====
def simular_partida_otimizada_integrada(clube1_stats, clube2_stats, nome1, nome2):
    """
    Versão otimizada da simulação que mantém compatibilidade
    com sua função original simular_partida_automatica
    """
    
    # Usar tanto habilidade_media quanto forca_geral para mais realismo
    hab1 = (clube1_stats['habilidade_media'] + clube1_stats['forca_geral']) / 2 + 2  # fator casa
    hab2 = (clube2_stats['habilidade_media'] + clube2_stats['forca_geral']) / 2
    prob1 = hab1 / (hab1 + hab2)
    
    # Simular gols (mesmo algoritmo da sua função original)
    gols1, gols2 = 0, 0
    num_chances = random.randint(4, 9)  # Seus valores originais
    
    for _ in range(num_chances):
        if random.random() < prob1:
            if random.random() < 0.45:  # Seus valores originais
                gols1 += 1
        else:
            if random.random() < 0.30:  # Seus valores originais
                gols2 += 1
    
    # Gol extra (sua lógica original)
    if random.random() < 0.20:  # Seus valores originais
        if random.random() < 0.5:
            gols1 += 1
        else:
            gols2 += 1
    
    # Selecionar artilheiros usando pesos pré-calculados
    artilheiros1 = selecionar_artilheiros_otimizado(clube1_stats, gols1, nome1)
    artilheiros2 = selecionar_artilheiros_otimizado(clube2_stats, gols2, nome2)
    
    # Criar marcadores formatados (compatível com sua função salvar_resultado)
    marcadores_formatados = []
    
    # Gols do time 1
    for i in range(gols1):
        if i < len(artilheiros1):
            jogador_nome = artilheiros1[i].split(' (')[0]  # Remover "(Nome do Time)"
            minuto = random.randint(1, 90)
            marcadores_formatados.append(f"{jogador_nome}:{minuto}:{nome1}")
    
    # Gols do time 2
    for i in range(gols2):
        if i < len(artilheiros2):
            jogador_nome = artilheiros2[i].split(' (')[0]  # Remover "(Nome do Time)"
            minuto = random.randint(1, 90)
            marcadores_formatados.append(f"{jogador_nome}:{minuto}:{nome2}")
    
    # Determinar vencedor
    if gols1 > gols2:
        vencedor = nome1
    elif gols2 > gols1:
        vencedor = nome2
    else:
        vencedor = "Empate"
    
    # Formato compatível com suas funções existentes
    return {
        'time_casa': nome1,
        'time_visitante': nome2,
        'gols_casa': gols1,
        'gols_visitante': gols2,
        'vencedor': vencedor,
        'artilheiros': artilheiros1 + artilheiros2,
        'marcadores_gols': ';'.join(marcadores_formatados),  # Formato para sua função salvar_resultado
        'marcadores_resumo': f"{nome1} {gols1} x {gols2} {nome2}",
        'data': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def selecionar_artilheiros_otimizado(clube_stats, num_gols, nome_clube):
    """Seleciona artilheiros usando pesos pré-calculados"""
    if num_gols == 0:
        return []
    
    jogadores = clube_stats['jogadores']
    pesos = clube_stats['pesos_posicao']
    
    # Criar lista ponderada uma única vez
    jogadores_ponderados = []
    for jogador, peso in zip(jogadores, pesos):
        jogadores_ponderados.extend([jogador] * peso)
    
    artilheiros = []
    for _ in range(num_gols):
        if jogadores_ponderados:
            jogador_gol = random.choice(jogadores_ponderados)
            artilheiros.append(f"{jogador_gol['nome']} ({nome_clube})")
    
    return artilheiros

# ===== 4. SIMULAÇÃO COM PROGRESS BAR =====
def simular_campeonato_integrado(clubes_stats, formato="todos_contra_todos", salvar_automatico=True):
    """Simula campeonato com barra de progresso e opção de salvar"""
    
    clubes_nomes = list(clubes_stats.keys())
    total_partidas = len(clubes_nomes) * (len(clubes_nomes) - 1)
    
    if formato == "ida_volta":
        total_partidas = total_partidas // 2
    
    # Criar barra de progresso
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    resultados = []
    partida_atual = 0
    
    for i, time1 in enumerate(clubes_nomes):
        for j, time2 in enumerate(clubes_nomes):
            if i != j:  # Time não joga contra si mesmo
                if formato == "ida_volta" and i > j:
                    continue  # Evitar jogos duplicados
                
                # Simular partida
                resultado = simular_partida_otimizada_integrada(
                    clubes_stats[time1], 
                    clubes_stats[time2],
                    time1,
                    time2
                )
                resultados.append(resultado)
                
                # Salvar automaticamente se solicitado
                if salvar_automatico:
                    try:
                        # Criar objetos clube compatíveis com sua função salvar_resultado
                        clube1_obj = {'nome': time1}
                        clube2_obj = {'nome': time2}
                        
                        # Extrair marcadores no formato esperado
                        marcadores_gols = []
                        for marcador in resultado['marcadores_gols'].split(';'):
                            if marcador and ':' in marcador:
                                partes = marcador.split(':')
                                if len(partes) == 3:
                                    marcadores_gols.append((partes[0], partes[1], partes[2]))
                        
                        salvar_resultado(
                            clube1_obj, 
                            clube2_obj, 
                            resultado['gols_casa'], 
                            resultado['gols_visitante'], 
                            marcadores_gols
                        )
                    except Exception as e:
                        st.warning(f"Erro ao salvar partida {time1} vs {time2}: {e}")
                
                # Atualizar progresso
                partida_atual += 1
                progresso = partida_atual / total_partidas
                progress_bar.progress(progresso)
                status_text.text(f'Simulando: {time1} vs {time2} ({partida_atual}/{total_partidas})')
    
    progress_bar.empty()
    status_text.empty()
    
    return resultados

# ===== 5. INTERFACE OTIMIZADA INTEGRADA =====
def interface_simulacao_otimizada_integrada():
    """Interface otimizada que usa suas funções existentes"""
    
    st.title("⚽ Simulador de Campeonato Otimizado")
    st.caption("Versão otimizada integrada com io.py")
    
    # Carregar dados (com cache)
    with st.spinner("Carregando dados dos clubes..."):
        clubes_data = carregar_dados_clubes()
        
        if not clubes_data:
            st.error("❌ Não foi possível carregar os dados dos clubes!")
            st.info("Verifique se os arquivos estão no local correto:")
            st.code("data/clubes_utf8.csv\ndata/jogadores_utf8.csv")
            return
        
        clubes_stats = calcular_estatisticas_pre_processadas(clubes_data)
    
    # Mostrar estatísticas dos dados carregados
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Clubes carregados", len(clubes_data))
    with col2:
        total_jogadores = sum(len(clube['jogadores']) for clube in clubes_data.values())
        st.metric("Total de jogadores", total_jogadores)
    with col3:
        media_jogadores = total_jogadores / len(clubes_data) if clubes_data else 0
        st.metric("Média jogadores/clube", f"{media_jogadores:.1f}")
    
    # Seleção de times
    clubes_disponiveis = list(clubes_stats.keys())
    clubes_selecionados = st.multiselect(
        "Selecione os clubes para o campeonato:",
        clubes_disponiveis,
        default=clubes_disponiveis[:min(4, len(clubes_disponiveis))]  # Primeiros 4 por padrão
    )
    
    if len(clubes_selecionados) < 2:
        st.warning("⚠️ Selecione pelo menos 2 clubes!")
        return
    
    # Opções de simulação
    col1, col2, col3 = st.columns(3)
    
    with col1:
        formato = st.selectbox(
            "Formato do campeonato:",
            ["todos_contra_todos", "ida_volta"]
        )
    
    with col2:
        salvar_automatico = st.checkbox("Salvar resultados automaticamente", value=True)
    
    with col3:
        estimativa_partidas = len(clubes_selecionados) * (len(clubes_selecionados) - 1)
        if formato == "ida_volta":
            estimativa_partidas = estimativa_partidas // 2
        st.metric("Partidas a simular", estimativa_partidas)
    
    # Botão de simulação
    if st.button("🚀 Simular Campeonato", type="primary"):
        
        start_time = time.time()
        
        # Filtrar clubes selecionados
        clubes_filtrados = {k: v for k, v in clubes_stats.items() if k in clubes_selecionados}
        
        # Simular campeonato
        resultados = simular_campeonato_integrado(
            clubes_filtrados, 
            formato, 
            salvar_automatico
        )
        
        end_time = time.time()
        
        # Exibir resultados
        st.success(f"✅ Simulação concluída em {end_time - start_time:.2f} segundos!")
        
        if salvar_automatico:
            st.info("💾 Resultados salvos automaticamente no histórico!")
        
        # Converter para DataFrame para melhor visualização
        df_resultados = pd.DataFrame(resultados)
        
        # Estatísticas do campeonato
        st.subheader("📊 Resultados do Campeonato")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de partidas", len(resultados))
        with col2:
            total_gols = df_resultados['gols_casa'].sum() + df_resultados['gols_visitante'].sum()
            st.metric("Total de gols", total_gols)
        with col3:
            media_gols = total_gols / len(resultados) if len(resultados) > 0 else 0
            st.metric("Média gols/partida", f"{media_gols:.2f}")
        with col4:
            empates = len(df_resultados[df_resultados['vencedor'] == 'Empate'])
            st.metric("Empates", empates)
        
        # Tabela de resultados
        st.subheader("🏆 Tabela de Resultados")
        st.dataframe(df_resultados, use_container_width=True)
        
        # Ranking dos times
        with st.expander("🏅 Ranking dos Times"):
            criar_ranking_times(df_resultados, clubes_selecionados)
        
        # Artilheiros
        with st.expander("⚽ Artilheiros do Campeonato"):
            mostrar_artilheiros(df_resultados)

def criar_ranking_times(df_resultados, clubes_nomes):
    """Cria ranking dos times baseado nos resultados"""
    ranking = {}
    
    for clube in clubes_nomes:
        jogos_casa = df_resultados[df_resultados['time_casa'] == clube]
        jogos_visitante = df_resultados[df_resultados['time_visitante'] == clube]
        
        pontos = 0
        vitorias = 0
        empates = 0
        derrotas = 0
        gols_pro = 0
        gols_contra = 0
        
        # Jogos em casa
        for _, jogo in jogos_casa.iterrows():
            gols_pro += jogo['gols_casa']
            gols_contra += jogo['gols_visitante']
            
            if jogo['gols_casa'] > jogo['gols_visitante']:
                pontos += 3
                vitorias += 1
            elif jogo['gols_casa'] == jogo['gols_visitante']:
                pontos += 1
                empates += 1
            else:
                derrotas += 1
        
        # Jogos como visitante
        for _, jogo in jogos_visitante.iterrows():
            gols_pro += jogo['gols_visitante']
            gols_contra += jogo['gols_casa']
            
            if jogo['gols_visitante'] > jogo['gols_casa']:
                pontos += 3
                vitorias += 1
            elif jogo['gols_visitante'] == jogo['gols_casa']:
                pontos += 1
                empates += 1
            else:
                derrotas += 1
        
        saldo = gols_pro - gols_contra
        jogos = vitorias + empates + derrotas
        
        ranking[clube] = {
            'Pontos': pontos,
            'Jogos': jogos,
            'Vitórias': vitorias,
            'Empates': empates,
            'Derrotas': derrotas,
            'Gols Pró': gols_pro,
            'Gols Contra': gols_contra,
            'Saldo': saldo
        }
    
    # Ordenar por pontos, depois por saldo de gols
    ranking_ordenado = sorted(ranking.items(), key=lambda x: (x[1]['Pontos'], x[1]['Saldo']), reverse=True)
    
    # Mostrar tabela
    df_ranking = pd.DataFrame([{**{'Time': time}, **stats} for time, stats in ranking_ordenado])
    st.dataframe(df_ranking, use_container_width=True)

def mostrar_artilheiros(df_resultados):
    """Mostra os artilheiros do campeonato"""
    artilheiros_count = {}
    
    for _, resultado in df_resultados.iterrows():
        for artilheiro in resultado['artilheiros']:
            if artilheiro in artilheiros_count:
                artilheiros_count[artilheiro] += 1
            else:
                artilheiros_count[artilheiro] = 1
    
    # Ordenar por número de gols
    artilheiros_ordenados = sorted(artilheiros_count.items(), key=lambda x: x[1], reverse=True)
    
    # Mostrar top 10
    top_artilheiros = artilheiros_ordenados[:10]
    
    for i, (jogador, gols) in enumerate(top_artilheiros, 1):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"{i}º {jogador}")
        with col2:
            st.write(f"⚽ {gols}")

# ===== 6. EXEMPLO DE USO =====
if __name__ == "__main__":
    interface_simulacao_otimizada_integrada()
