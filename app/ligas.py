# Arquivo: app/ligas.py - VERSÃO COM ARTILHEIROS
import streamlit as st
import pandas as pd
import json
import os
import random
from datetime import datetime, timedelta
from utils.io import carregar_historico  # APENAS esta função existe
from app.simulacao_otimizada import simular_partida_automatica
import time

def criar_diretorio_ligas():
    """Cria o diretório para armazenar dados das ligas se não existir."""
    os.makedirs("data/ligas", exist_ok=True)

def salvar_historico_compativel(novo_historico):
    """
    Função compatível para salvar histórico usando pandas com cabeçalho correto.
    Segue o formato: data,time_casa,time_visitante,gols_casa,gols_visitante,vencedor,marcadores_gols,artilheiros
    """
    try:
        arquivo_historico = "data/historico_partidas.csv"
        
        # Garantir que as colunas estão na ordem correta
        colunas_corretas = ['data', 'time_casa', 'time_visitante', 'gols_casa', 'gols_visitante', 'vencedor', 'marcadores_gols', 'artilheiros']
        
        # Reordenar colunas se necessário
        if set(novo_historico.columns) == set(colunas_corretas):
            novo_historico = novo_historico[colunas_corretas]
        
        novo_historico.to_csv(arquivo_historico, index=False, encoding='utf-8')
        return True
    except Exception as e:
        st.error(f"Erro ao salvar histórico: {e}")
        return False

def determinar_vencedor_partida(gols_casa, gols_visitante, time_casa, time_visitante):
    """Determina o vencedor de uma partida."""
    if gols_casa > gols_visitante:
        return time_casa
    elif gols_visitante > gols_casa:
        return time_visitante
    else:
        return "Empate"

def calcular_artilheiros_liga(partidas):
    """
    Calcula os artilheiros da liga baseado nos resultados das partidas.
    
    Args:
        partidas: Lista de dicionários com os resultados das partidas
    
    Returns:
        list: Lista ordenada de tuplas (jogador, time, gols) dos artilheiros
    """
    contagem_gols = {}
    
    for partida in partidas:
        # Extrair artilheiros da partida
        artilheiros = partida.get('artilheiros', [])
        
        for artilheiro in artilheiros:
            if artilheiro:  # Verificar se não está vazio
                # O formato é "Nome do Jogador (Nome do Time)"
                if '(' in artilheiro and ')' in artilheiro:
                    nome_completo = artilheiro.strip()
                    # Separar nome do jogador do time
                    try:
                        nome_jogador = nome_completo.split(' (')[0].strip()
                        nome_time = nome_completo.split(' (')[1].replace(')', '').strip()
                        
                        # Chave única: jogador + time (caso haja jogadores com mesmo nome)
                        chave_jogador = f"{nome_jogador}|{nome_time}"
                        
                        if chave_jogador in contagem_gols:
                            contagem_gols[chave_jogador]['gols'] += 1
                        else:
                            contagem_gols[chave_jogador] = {
                                'nome': nome_jogador,
                                'time': nome_time,
                                'gols': 1
                            }
                    except IndexError:
                        # Se houver problema no formato, pular este artilheiro
                        continue
    
    # Converter para lista e ordenar por número de gols
    artilheiros_ordenados = []
    for dados in contagem_gols.values():
        artilheiros_ordenados.append((dados['nome'], dados['time'], dados['gols']))
    
    # Ordenar por gols (decrescente), depois por nome (crescente)
    artilheiros_ordenados.sort(key=lambda x: (-x[2], x[0]))
    
    return artilheiros_ordenados

def exibir_artilheiros_liga(partidas, clubes, top_n=20):
    """
    Exibe os artilheiros da liga com formatação visual atraente.
    
    Args:
        partidas: Lista com os resultados das partidas
        clubes: Dicionário com dados dos clubes (para logos)
        top_n: Número de artilheiros a exibir (padrão: 20)
    """
    st.subheader("⚽ Artilheiros da Liga")
    
    # Calcular artilheiros
    artilheiros = calcular_artilheiros_liga(partidas)
    
    if not artilheiros:
        st.warning("Nenhum gol foi registrado na liga.")
        return
    
    # Limitar ao top N
    top_artilheiros = artilheiros[:top_n]
    
    # Estatísticas gerais
    total_gols = sum(dados[2] for dados in artilheiros)
    total_artilheiros = len(artilheiros)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("⚽ Total de Gols", total_gols)
    with col2:
        st.metric("👤 Jogadores que Marcaram", total_artilheiros)
    with col3:
        if top_artilheiros:
            artilheiro_maximo = top_artilheiros[0]
            st.metric("🥇 Artilheiro", f"{artilheiro_maximo[0]} - {artilheiro_maximo[2]} gols")
    
    # Tabela de artilheiros
    st.markdown("### 🏆 Top 20 Artilheiros")
    
    # Cabeçalho da tabela
    cols = st.columns([0.8, 3.5, 2.5, 1.2])
    headers = ["#", "Jogador", "Time", "Gols"]
    
    for col, header in zip(cols, headers):
        col.markdown(f"**{header}**")
    
    # Linhas da tabela
    for idx, (nome_jogador, nome_time, gols) in enumerate(top_artilheiros):
        cols = st.columns([0.8, 3.5, 2.5, 1.2])
        
        # Posição com emoji especial para os primeiros
        if idx == 0:
            cols[0].markdown("🥇")
        elif idx == 1:
            cols[0].markdown("🥈")
        elif idx == 2:
            cols[0].markdown("🥉")
        else:
            cols[0].write(f"**{idx + 1}º**")
        
        # Nome do jogador
        cols[1].markdown(f"**{nome_jogador}**")
        
        # Time com logo (se disponível)
        logo_html = ""
        for clube in clubes.values():
            if clube['nome'] == nome_time and clube.get('logo_base64'):
                logo_html = f'<img src="data:image/png;base64,{clube["logo_base64"]}" style="width: 20px; height: 20px; margin-right: 8px; vertical-align: middle;">'
                break
        
        cols[2].markdown(f'{logo_html}{nome_time}', unsafe_allow_html=True)
        
        # Número de gols com destaque
        if gols >= 10:
            cols[3].markdown(f'<span style="color: #ff6b6b; font-weight: bold; font-size: 1.1em;">{gols}</span>', unsafe_allow_html=True)
        elif gols >= 5:
            cols[3].markdown(f'<span style="color: #4ecdc4; font-weight: bold;">{gols}</span>', unsafe_allow_html=True)
        else:
            cols[3].markdown(f'**{gols}**')
    
    # Estatísticas adicionais em expander
    with st.expander("📊 Estatísticas Detalhadas dos Artilheiros"):
        
        # Distribuição por time
        st.markdown("#### 🏟️ Gols por Time")
        gols_por_time = {}
        for nome_jogador, nome_time, gols in artilheiros:
            if nome_time in gols_por_time:
                gols_por_time[nome_time] += gols
            else:
                gols_por_time[nome_time] = gols
        
        # Ordenar times por total de gols
        times_ordenados = sorted(gols_por_time.items(), key=lambda x: x[1], reverse=True)
        
        for i, (time, total_gols) in enumerate(times_ordenados):
            col1, col2 = st.columns([3, 1])
            with col1:
                # Buscar logo do time
                logo_html = ""
                for clube in clubes.values():
                    if clube['nome'] == time and clube.get('logo_base64'):
                        logo_html = f'<img src="data:image/png;base64,{clube["logo_base64"]}" style="width: 20px; height: 20px; margin-right: 8px; vertical-align: middle;">'
                        break
                st.markdown(f"{i+1}º {logo_html}{time}", unsafe_allow_html=True)
            with col2:
                st.markdown(f"**{total_gols} gols**")
        
        # Estatísticas de distribuição
        st.markdown("#### 📈 Distribuição de Gols")
        
        if artilheiros:
            max_gols = max(dados[2] for dados in artilheiros)
            min_gols = min(dados[2] for dados in artilheiros)
            media_gols = total_gols / total_artilheiros
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Maior Artilheiro", f"{max_gols} gols")
            with col2:
                st.metric("Menor Artilheiro", f"{min_gols} gol{'s' if min_gols > 1 else ''}")
            with col3:
                st.metric("Média por Jogador", f"{media_gols:.1f} gols")
            
            # Distribuição por faixas de gols
            faixas = {
                "10+ gols": len([x for x in artilheiros if x[2] >= 10]),
                "5-9 gols": len([x for x in artilheiros if 5 <= x[2] <= 9]),
                "3-4 gols": len([x for x in artilheiros if 3 <= x[2] <= 4]),
                "1-2 gols": len([x for x in artilheiros if 1 <= x[2] <= 2])
            }
            
            st.markdown("**Jogadores por faixa de gols:**")
            for faixa, quantidade in faixas.items():
                if quantidade > 0:
                    st.write(f"• {faixa}: {quantidade} jogador{'es' if quantidade > 1 else ''}")

def salvar_historico_liga(dados_liga):
    """Salva o histórico de uma liga realizada."""
    criar_diretorio_ligas()
    arquivo = "data/ligas/historico_ligas.json"
    
    try:
        # Tentar carregar histórico existente
        if os.path.exists(arquivo):
            with open(arquivo, 'r', encoding='utf-8') as f:
                historico = json.load(f)
        else:
            historico = []
        
        # Adicionar nova liga
        historico.append(dados_liga)
        
        # Salvar histórico atualizado
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(historico, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        st.error(f"Erro ao salvar histórico da liga: {e}")
        return False

def carregar_historico_ligas():
    """Carrega o histórico de ligas realizadas."""
    arquivo = "data/ligas/historico_ligas.json"
    
    try:
        if os.path.exists(arquivo):
            with open(arquivo, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        st.error(f"Erro ao carregar histórico de ligas: {e}")
        return []

def gerar_tabela_liga(partidas, times):
    """Gera a tabela de classificação da liga."""
    classificacao = {}
    
    # Inicializar estatísticas para todos os times
    for time in times:
        classificacao[time] = {
            'time': time,
            'pontos': 0,
            'jogos': 0,
            'vitorias': 0,
            'empates': 0,
            'derrotas': 0,
            'gols_pro': 0,
            'gols_contra': 0,
            'saldo': 0
        }
    
    # Processar cada partida
    for partida in partidas:
        time_casa = partida['time_casa']
        time_visitante = partida['time_visitante']
        gols_casa = partida['gols_casa']
        gols_visitante = partida['gols_visitante']
        
        # Atualizar estatísticas do time da casa
        classificacao[time_casa]['jogos'] += 1
        classificacao[time_casa]['gols_pro'] += gols_casa
        classificacao[time_casa]['gols_contra'] += gols_visitante
        
        # Atualizar estatísticas do time visitante
        classificacao[time_visitante]['jogos'] += 1
        classificacao[time_visitante]['gols_pro'] += gols_visitante
        classificacao[time_visitante]['gols_contra'] += gols_casa
        
        # Determinar resultado
        if gols_casa > gols_visitante:
            # Vitória do mandante
            classificacao[time_casa]['vitorias'] += 1
            classificacao[time_casa]['pontos'] += 3
            classificacao[time_visitante]['derrotas'] += 1
        elif gols_casa < gols_visitante:
            # Vitória do visitante
            classificacao[time_visitante]['vitorias'] += 1
            classificacao[time_visitante]['pontos'] += 3
            classificacao[time_casa]['derrotas'] += 1
        else:
            # Empate
            classificacao[time_casa]['empates'] += 1
            classificacao[time_casa]['pontos'] += 1
            classificacao[time_visitante]['empates'] += 1
            classificacao[time_visitante]['pontos'] += 1
    
    # Calcular saldo de gols
    for stats in classificacao.values():
        stats['saldo'] = stats['gols_pro'] - stats['gols_contra']
    
    # Converter para DataFrame e ordenar
    df = pd.DataFrame(list(classificacao.values()))
    df = df.sort_values(['pontos', 'saldo', 'gols_pro'], ascending=False)
    df.reset_index(drop=True, inplace=True)
    df.index += 1  # Começar classificação em 1
    
    return df

def simular_liga_completa(times_selecionados, clubes, ida_volta=False):
    """Simula uma liga completa entre os times selecionados."""
    partidas = []
    
    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Gerar todas as combinações de jogos
    combinacoes = []
    for i, time1 in enumerate(times_selecionados):
        for j, time2 in enumerate(times_selecionados):
            if i != j:
                combinacoes.append((time1, time2))
    
    # Se não for ida e volta, manter apenas um jogo entre cada dupla
    if not ida_volta:
        combinacoes_unicas = []
        jogos_realizados = set()
        for time1, time2 in combinacoes:
            par = tuple(sorted([time1, time2]))
            if par not in jogos_realizados:
                combinacoes_unicas.append((time1, time2))
                jogos_realizados.add(par)
        combinacoes = combinacoes_unicas
    
    # Simular todas as partidas
    total_partidas = len(combinacoes)
    
    for i, (nome_time1, nome_time2) in enumerate(combinacoes):
        # Encontrar os dados dos clubes
        clube1 = next(c for c in clubes.values() if c['nome'] == nome_time1)
        clube2 = next(c for c in clubes.values() if c['nome'] == nome_time2)
        
        # Simular partida
        resultado = simular_partida_automatica(clube1, clube2)
        partidas.append(resultado)
        
        # Atualizar progress
        progresso = (i + 1) / total_partidas
        progress_bar.progress(progresso)
        status_text.text(f"Simulando: {nome_time1} vs {nome_time2} ({i+1}/{total_partidas})")
        
        # Pequena pausa para efeito visual
        time.sleep(0.1)
    
    progress_bar.empty()
    status_text.empty()
    
    return partidas

def exibir_classificacao_liga_com_logos(tabela, clubes):
    """Exibe a tabela de classificação da liga com logos dos times."""
    st.subheader("📊 Classificação Final da Liga")
    
    # Cabeçalho da tabela
    cols = st.columns([0.8, 3, 1, 1, 1, 1, 1, 1.5, 1.5, 1.5])
    headers = ["#", "Time", "J", "V", "E", "D", "GP", "GC", "SG", "PTS"]
    
    for col, header in zip(cols, headers):
        col.markdown(f"**{header}**")
    
    # Linhas da tabela
    for idx, (_, row) in enumerate(tabela.iterrows()):
        cols = st.columns([0.8, 3, 1, 1, 1, 1, 1, 1.5, 1.5, 1.5])
        
        # Posição
        cols[0].write(f"**{idx + 1}º**")
        
        # Time com logo
        time_nome = row['time']
        logo_html = ""
        for clube in clubes.values():
            if clube['nome'] == time_nome and clube.get('logo_base64'):
                logo_html = f'<img src="data:image/png;base64,{clube["logo_base64"]}" style="width: 20px; height: 20px; margin-right: 8px; vertical-align: middle;">'
                break
        
        # Destacar campeão e vice
        if idx == 0:  # Campeão
            cols[1].markdown(f'{logo_html}<span style="color: gold; font-weight: bold;">👑 {time_nome}</span>', unsafe_allow_html=True)
        elif idx == 1:  # Vice-campeão
            cols[1].markdown(f'{logo_html}<span style="color: silver; font-weight: bold;">🥈 {time_nome}</span>', unsafe_allow_html=True)
        else:
            cols[1].markdown(f'{logo_html}<span style="font-weight: bold;">{time_nome}</span>', unsafe_allow_html=True)
        
        # Outras estatísticas
        cols[2].write(str(row['jogos']))
        cols[3].write(str(row['vitorias']))
        cols[4].write(str(row['empates']))
        cols[5].write(str(row['derrotas']))
        cols[6].write(str(row['gols_pro']))
        cols[7].write(str(row['gols_contra']))
        
        # Saldo de gols com cor
        saldo = row['saldo']
        if saldo > 0:
            cols[8].markdown(f'<span style="color: green;">+{saldo}</span>', unsafe_allow_html=True)
        elif saldo < 0:
            cols[8].markdown(f'<span style="color: red;">{saldo}</span>', unsafe_allow_html=True)
        else:
            cols[8].write("0")
        
        # Pontos
        cols[9].markdown(f"**{row['pontos']}**")

def pagina_ligas(clubes):
    """Página principal do módulo de ligas."""
    st.header("🏆 Simulador de Ligas")
    
    # Verificar se há clubes suficientes
    if len(clubes) < 4:
        st.error("❌ É necessário ter pelo menos 4 times para criar uma liga.")
        return
    
    # Inicializar session_state se necessário
    if 'times_sorteados' not in st.session_state:
        st.session_state.times_sorteados = []
    if 'num_times_liga' not in st.session_state:
        st.session_state.num_times_liga = 0
    
    # Seção de configuração da liga
    st.subheader("⚙️ Configuração da Liga")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Seleção do número de times
        max_times = min(len(clubes), 20)  # Limitar a 20 times para performance
        num_times = st.slider(
            "Número de times na liga:",
            min_value=4,
            max_value=max_times,
            value=min(8, max_times),
            help="Escolha quantos times participarão da liga"
        )
        
        # Se mudou o número de times, limpar sorteio anterior
        if num_times != st.session_state.num_times_liga:
            st.session_state.times_sorteados = []
            st.session_state.num_times_liga = num_times
    
    with col2:
        # Opção ida e volta
        ida_volta = st.checkbox(
            "Jogos de ida e volta",
            value=True,
            help="Se marcado, cada time jogará duas vezes contra cada adversário"
        )
    
    # Seleção manual dos times ou aleatória
    st.subheader("👥 Seleção dos Times")
    
    opcao_selecao = st.radio(
        "Como selecionar os times:",
        ["Seleção manual", "Seleção aleatória"],
        horizontal=True
    )
    
    times_selecionados = []
    
    if opcao_selecao == "Seleção manual":
        # Limpar sorteio quando muda para manual
        if st.session_state.times_sorteados:
            st.session_state.times_sorteados = []
        
        # Permitir seleção manual dos times
        opcoes_clubes = [(nome, dados['nome']) for nome, dados in clubes.items()]
        
        times_selecionados_ids = st.multiselect(
            f"Selecione {num_times} times para a liga:",
            options=opcoes_clubes,
            format_func=lambda x: x[1],
            max_selections=num_times
        )
        
        times_selecionados = [clubes[tid[0]]['nome'] for tid in times_selecionados_ids]
        
        if len(times_selecionados) < num_times:
            st.warning(f"⚠️ Selecione exatamente {num_times} times para continuar.")
            return
    
    else:  # Seleção aleatória
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("🎲 Sortear times aleatoriamente", type="secondary"):
                times_aleatorios = random.sample(list(clubes.keys()), num_times)
                st.session_state.times_sorteados = [clubes[tid]['nome'] for tid in times_aleatorios]
        
        with col2:
            if st.session_state.times_sorteados:
                if st.button("🔄 Sortear novamente", type="secondary"):
                    times_aleatorios = random.sample(list(clubes.keys()), num_times)
                    st.session_state.times_sorteados = [clubes[tid]['nome'] for tid in times_aleatorios]
        
        # Usar times sorteados do session_state
        if st.session_state.times_sorteados and len(st.session_state.times_sorteados) == num_times:
            times_selecionados = st.session_state.times_sorteados
            
            st.success(f"✅ Times sorteados para a liga:")
            cols = st.columns(min(4, len(times_selecionados)))
            for i, nome_time in enumerate(times_selecionados):
                with cols[i % len(cols)]:
                    # Mostrar logo se disponível
                    for clube in clubes.values():
                        if clube['nome'] == nome_time and clube.get('logo_base64'):
                            st.markdown(
                                f"""<div style="text-align: center;">
                                <img src="data:image/png;base64,{clube['logo_base64']}" 
                                style="width: 40px; height: 40px; margin-bottom: 5px;"><br>
                                <small>{nome_time}</small>
                                </div>""",
                                unsafe_allow_html=True
                            )
                            break
                    else:
                        st.write(f"⚽ {nome_time}")
        else:
            if not st.session_state.times_sorteados:
                st.info("🎲 Clique em 'Sortear times aleatoriamente' para começar!")
            return
    
    # Se temos times selecionados, mostrar informações da liga
    if len(times_selecionados) == num_times:
        st.markdown("---")
        
        # Informações da liga
        total_jogos = (num_times * (num_times - 1))
        if not ida_volta:
            total_jogos //= 2
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("👥 Times Participantes", num_times)
        with col2:
            st.metric("⚽ Total de Jogos", total_jogos)
        with col3:
            formato = "Ida e Volta" if ida_volta else "Turno Único"
            st.metric("🔄 Formato", formato)
        
        # Botão para simular a liga
        if st.button("🚀 Simular Liga Completa", type="primary", use_container_width=True):
            with st.spinner("🔄 Simulando liga..."):
                # Limpar times sorteados após simular
                st.session_state.times_sorteados = []
                
                # Simular todas as partidas
                partidas = simular_liga_completa(times_selecionados, clubes, ida_volta)
                
                # Salvar partidas no histórico geral
                historico_atual = carregar_historico()
                if historico_atual is not None:
                    # Adicionar partidas ao histórico existente no formato correto
                    novas_linhas = []
                    for partida in partidas:
                        nova_linha = {
                            'data': partida['data'],
                            'time_casa': partida['time_casa'],
                            'time_visitante': partida['time_visitante'],
                            'gols_casa': partida['gols_casa'],
                            'gols_visitante': partida['gols_visitante'],
                            'vencedor': partida['vencedor'],
                            'marcadores_gols': partida['marcadores_gols'],  # Já no formato correto: Nome:Minuto:Time;Nome:Minuto:Time
                            'artilheiros': ''  # Deixar vazio conforme formato padrão
                        }
                        novas_linhas.append(nova_linha)
                    
                    # Criar DataFrame com as novas partidas
                    novas_partidas_df = pd.DataFrame(novas_linhas)
                    
                    # Verificar se o histórico atual tem as colunas certas
                    if historico_atual.empty or 'vencedor' not in historico_atual.columns:
                        # Se histórico está vazio ou não tem as colunas certas, criar novo
                        novo_historico = novas_partidas_df
                    else:
                        # Garantir que o histórico existente tem todas as colunas necessárias
                        colunas_necessarias = ['data', 'time_casa', 'time_visitante', 'gols_casa', 'gols_visitante', 'vencedor', 'marcadores_gols', 'artilheiros']
                        
                        for coluna in colunas_necessarias:
                            if coluna not in historico_atual.columns:
                                if coluna == 'vencedor':
                                    # Calcular vencedor para registros antigos
                                    historico_atual[coluna] = historico_atual.apply(
                                        lambda row: determinar_vencedor_partida(
                                            row['gols_casa'], 
                                            row['gols_visitante'], 
                                            row['time_casa'], 
                                            row['time_visitante']
                                        ), axis=1
                                    )
                                elif coluna == 'marcadores_gols':
                                    # Para registros antigos sem marcadores_gols, deixar vazio
                                    historico_atual[coluna] = ''
                                else:
                                    historico_atual[coluna] = ''
                        
                        # Concatenar com histórico existente
                        novo_historico = pd.concat([historico_atual, novas_partidas_df], ignore_index=True)
                    
                    # Salvar no histórico usando função compatível
                    salvar_historico_compativel(novo_historico)
                
                # Gerar tabela de classificação
                tabela = gerar_tabela_liga(partidas, times_selecionados)
                
                # Exibir resultados
                st.success("🎉 Liga simulada com sucesso!")
                
                # Mostrar campeão e vice
                campeao = tabela.iloc[0]['time']
                vice = tabela.iloc[1]['time']
                
                # Banner de comemoração
                st.markdown(
                    f"""
                    <div style="background: linear-gradient(90deg, #FFD700, #FFA500); 
                                padding: 20px; border-radius: 10px; text-align: center; margin: 20px 0;">
                        <h2 style="color: #000; margin: 0;">🏆 CAMPEÃO DA LIGA</h2>
                        <h1 style="color: #000; margin: 10px 0;">{campeao}</h1>
                        <h3 style="color: #333; margin: 0;">🥈 Vice-campeão: {vice}</h3>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Exibir classificação completa
                exibir_classificacao_liga_com_logos(tabela, clubes)
                
                # ===== NOVA FUNCIONALIDADE: EXIBIR ARTILHEIROS =====
                st.markdown("---")
                exibir_artilheiros_liga(partidas, clubes, top_n=20)
                
                # Salvar dados da liga no histórico (agora incluindo artilheiros)
                artilheiros_liga = calcular_artilheiros_liga(partidas)
                
                dados_liga = {
                    'data': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'times_participantes': times_selecionados,
                    'formato': 'Ida e Volta' if ida_volta else 'Turno Único',
                    'total_jogos': len(partidas),
                    'campeao': campeao,
                    'vice': vice,
                    'classificacao_completa': tabela.to_dict('records'),
                    'artilheiros': artilheiros_liga[:10],  # Salvar top 10 artilheiros
                    'partidas': partidas
                }
                
                if salvar_historico_liga(dados_liga):
                    st.success("💾 Liga salva no histórico!")

def exibir_hall_da_fama_ligas(clubes):
    """Exibe o hall da fama das ligas (campeões, vices e artilheiros)."""
    st.header("👑 Hall da Fama - Ligas")
    
    historico = carregar_historico_ligas()
    
    if not historico:
        st.info("📝 Nenhuma liga foi realizada ainda. Simule uma liga primeiro!")
        return
    
    # Contar títulos, vices e artilheiros
    titulos = {}
    vices = {}
    artilheiros_historicos = {}  # Contador geral de gols por jogador
    artilheiros_por_liga = []    # Lista de artilheiros de cada liga
    
    for i, liga in enumerate(historico):
        campeao = liga.get('campeao', '')
        vice = liga.get('vice', '')
        
        # Contar títulos e vices
        if campeao:
            titulos[campeao] = titulos.get(campeao, 0) + 1
        if vice:
            vices[vice] = vices.get(vice, 0) + 1
        
        # Processar artilheiros da liga
        artilheiros_liga = liga.get('artilheiros', [])
        if artilheiros_liga:
            # Encontrar o artilheiro principal (primeiro da lista)
            if len(artilheiros_liga) > 0:
                principal = artilheiros_liga[0]
                if len(principal) >= 3:  # (nome, time, gols)
                    artilheiro_info = {
                        'liga_numero': i + 1,
                        'data': liga.get('data', 'Data não disponível'),
                        'nome': principal[0],
                        'time': principal[1], 
                        'gols': principal[2],
                        'formato': liga.get('formato', 'N/A')
                    }
                    artilheiros_por_liga.append(artilheiro_info)
            
            # Contar gols históricos de todos os jogadores
            for artilheiro_data in artilheiros_liga:
                if len(artilheiro_data) >= 3:
                    nome = artilheiro_data[0]
                    time = artilheiro_data[1]
                    gols = artilheiro_data[2]
                    
                    # Chave única para jogador
                    chave_jogador = f"{nome}|{time}"
                    
                    if chave_jogador in artilheiros_historicos:
                        artilheiros_historicos[chave_jogador]['gols_total'] += gols
                        artilheiros_historicos[chave_jogador]['ligas_participou'] += 1
                    else:
                        artilheiros_historicos[chave_jogador] = {
                            'nome': nome,
                            'time': time,
                            'gols_total': gols,
                            'ligas_participou': 1
                        }
    
    # Exibir estatísticas gerais
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🏆 Ligas Realizadas", len(historico))
    with col2:
        st.metric("👑 Times Campeões", len(titulos))
    with col3:
        st.metric("🥈 Times Vice-campeões", len(vices))
    with col4:
        total_artilheiros = len(artilheiros_historicos)
        st.metric("⚽ Artilheiros Únicos", total_artilheiros)
    
    # Criar abas para diferentes seções
    tab1, tab2, tab3, tab4 = st.tabs(["🏆 Campeões", "🥈 Vice-campeões", "⚽ Artilheiros Históricos", "📚 Histórico Completo"])
    
    # ===== ABA 1: CAMPEÕES =====
    with tab1:
        if titulos:
            st.subheader("🏆 Ranking de Campeões")
            campeoes_ordenados = sorted(titulos.items(), key=lambda x: x[1], reverse=True)
            
            for i, (time, quantidade) in enumerate(campeoes_ordenados):
                # Buscar logo do time
                logo_html = ""
                for clube in clubes.values():
                    if clube['nome'] == time and clube.get('logo_base64'):
                        logo_html = f'<img src="data:image/png;base64,{clube["logo_base64"]}" style="width: 25px; height: 25px; margin-right: 8px; vertical-align: middle;">'
                        break
                
                # Emoji especial para os primeiros colocados
                if i == 0:
                    emoji = "👑"
                elif i == 1:
                    emoji = "🥇"
                elif i == 2:
                    emoji = "🥈"
                else:
                    emoji = "🏆"
                
                st.markdown(
                    f"""<div style="display: flex; align-items: center; margin-bottom: 10px; 
                                 padding: 10px; background-color: #f0f2f6; border-radius: 5px;">
                       <div style="width: 30px;">{emoji}</div>
                       {logo_html}
                       <div style="flex: 1; font-weight: bold;">{time}</div>
                       <div style="width: 80px; text-align: right; font-weight: bold;">
                           {quantidade} título{'s' if quantidade > 1 else ''}
                       </div>
                    </div>""",
                    unsafe_allow_html=True
                )
    
    # ===== ABA 2: VICE-CAMPEÕES =====
    with tab2:
        if vices:
            st.subheader("🥈 Ranking de Vice-campeões")
            vices_ordenados = sorted(vices.items(), key=lambda x: x[1], reverse=True)
            
            for time, quantidade in vices_ordenados:
                # Buscar logo do time
                logo_html = ""
                for clube in clubes.values():
                    if clube['nome'] == time and clube.get('logo_base64'):
                        logo_html = f'<img src="data:image/png;base64,{clube["logo_base64"]}" style="width: 25px; height: 25px; margin-right: 8px; vertical-align: middle;">'
                        break
                
                st.markdown(
                    f"""<div style="display: flex; align-items: center; margin-bottom: 8px; 
                                 padding: 8px; background-color: #f8f9fa; border-radius: 5px;">
                       <div style="width: 30px;">🥈</div>
                       {logo_html}
                       <div style="flex: 1;">{time}</div>
                       <div style="width: 80px; text-align: right;">
                           {quantidade} vice{'s' if quantidade > 1 else ''}
                       </div>
                    </div>""",
                    unsafe_allow_html=True
                )
    
    # ===== ABA 3: ARTILHEIROS HISTÓRICOS =====
    with tab3:
        # Seção 1: Ranking Geral de Artilheiros
        if artilheiros_historicos:
            st.subheader("🏅 Ranking Histórico de Artilheiros")
            st.caption("Jogadores com mais gols em todas as ligas realizadas")
            
            # Ordenar por gols totais
            artilheiros_ordenados = sorted(
                artilheiros_historicos.values(), 
                key=lambda x: (-x['gols_total'], -x['ligas_participou'], x['nome'])
            )
            
            # Exibir top 15 artilheiros históricos
            top_artilheiros = artilheiros_ordenados[:15]
            
            # Cabeçalho da tabela
            cols = st.columns([0.8, 3, 2.5, 1.2, 1.5])
            headers = ["#", "Jogador", "Time", "Gols", "Ligas"]
            
            for col, header in zip(cols, headers):
                col.markdown(f"**{header}**")
            
            # Linhas da tabela
            for idx, artilheiro in enumerate(top_artilheiros):
                cols = st.columns([0.8, 3, 2.5, 1.2, 1.5])
                
                # Posição com medalhas
                if idx == 0:
                    cols[0].markdown("🥇")
                elif idx == 1:
                    cols[0].markdown("🥈")
                elif idx == 2:
                    cols[0].markdown("🥉")
                else:
                    cols[0].write(f"**{idx + 1}º**")
                
                # Nome do jogador
                cols[1].markdown(f"**{artilheiro['nome']}**")
                
                # Time com logo
                nome_time = artilheiro['time']
                logo_html = ""
                for clube in clubes.values():
                    if clube['nome'] == nome_time and clube.get('logo_base64'):
                        logo_html = f'<img src="data:image/png;base64,{clube["logo_base64"]}" style="width: 20px; height: 20px; margin-right: 8px; vertical-align: middle;">'
                        break
                
                cols[2].markdown(f'{logo_html}{nome_time}', unsafe_allow_html=True)
                
                # Gols com destaque
                gols_total = artilheiro['gols_total']
                if gols_total >= 20:
                    cols[3].markdown(f'<span style="color: #ff6b6b; font-weight: bold; font-size: 1.1em;">{gols_total}</span>', unsafe_allow_html=True)
                elif gols_total >= 10:
                    cols[3].markdown(f'<span style="color: #4ecdc4; font-weight: bold;">{gols_total}</span>', unsafe_allow_html=True)
                else:
                    cols[3].markdown(f'**{gols_total}**')
                
                # Número de ligas
                ligas_participou = artilheiro['ligas_participou']
                cols[4].write(f"{ligas_participou} liga{'s' if ligas_participou > 1 else ''}")
        
        # Seção 2: Artilheiros por Liga
        st.markdown("---")
        if artilheiros_por_liga:
            st.subheader("🏆 Artilheiros por Edição")
            st.caption("Jogador que mais marcou gols em cada liga realizada")
            
            # Reverter ordem para mostrar as ligas mais recentes primeiro
            artilheiros_por_liga_reversed = list(reversed(artilheiros_por_liga))
            
            for artilheiro in artilheiros_por_liga_reversed:
                # Container para cada liga
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        # Buscar logo do time
                        logo_html = ""
                        for clube in clubes.values():
                            if clube['nome'] == artilheiro['time'] and clube.get('logo_base64'):
                                logo_html = f'<img src="data:image/png;base64,{clube["logo_base64"]}" style="width: 25px; height: 25px; margin-right: 8px; vertical-align: middle;">'
                                break
                        
                        st.markdown(
                            f"""<div style="padding: 12px; background-color: #f8f9fa; border-radius: 8px; margin-bottom: 8px;">
                               <div style="display: flex; align-items: center;">
                                   <div style="margin-right: 15px;">
                                       <strong>Liga #{artilheiro['liga_numero']}</strong><br>
                                       <small style="color: #666;">{artilheiro['data'][:10]}</small>
                                   </div>
                                   <div style="margin-right: 15px;">⚽</div>
                                   {logo_html}
                                   <div>
                                       <strong>{artilheiro['nome']}</strong><br>
                                       <small>{artilheiro['time']}</small>
                                   </div>
                               </div>
                            </div>""",
                            unsafe_allow_html=True
                        )
                    
                    with col2:
                        st.markdown(
                            f"""<div style="text-align: center; padding: 12px;">
                               <div style="font-size: 1.5em; font-weight: bold; color: #ff6b6b;">
                                   {artilheiro['gols']}
                               </div>
                               <div style="font-size: 0.8em; color: #666;">
                                   gol{'s' if artilheiro['gols'] > 1 else ''}
                               </div>
                            </div>""",
                            unsafe_allow_html=True
                        )
        else:
            st.info("📊 Nenhum dado de artilheiro encontrado nas ligas anteriores.")
    
    # ===== ABA 4: HISTÓRICO COMPLETO =====
    with tab4:
        st.subheader("📚 Histórico Completo de Ligas")
        
        for i, liga in enumerate(reversed(historico), 1):
            data = liga.get('data', 'Data não disponível')
            campeao = liga.get('campeao', 'N/A')
            vice = liga.get('vice', 'N/A')
            formato = liga.get('formato', 'N/A')
            total_jogos = liga.get('total_jogos', 'N/A')
            
            # Encontrar artilheiro desta liga
            artilheiro_info = None
            for art in artilheiros_por_liga:
                if art['liga_numero'] == len(historico) - i + 1:
                    artilheiro_info = art
                    break
            
            # Container para cada liga
            with st.expander(f"🏆 Liga #{len(historico) - i + 1} - {data[:10]}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"""
                    **🏆 Campeão:** {campeao}
                    **🥈 Vice:** {vice}
                    **📊 Formato:** {formato}
                    **⚽ Total de jogos:** {total_jogos}
                    """)
                
                with col2:
                    if artilheiro_info:
                        # Buscar logo do time do artilheiro
                        logo_html = ""
                        for clube in clubes.values():
                            if clube['nome'] == artilheiro_info['time'] and clube.get('logo_base64'):
                                logo_html = f'<img src="data:image/png;base64,{clube["logo_base64"]}" style="width: 20px; height: 20px; margin-right: 8px; vertical-align: middle;">'
                                break
                        
                        st.markdown(f"""
                        **⚽ Artilheiro:** {artilheiro_info['nome']}
                        **🏟️ Time:** {logo_html}{artilheiro_info['time']}
                        **🥅 Gols:** {artilheiro_info['gols']}
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("**⚽ Artilheiro:** Dados não disponíveis")
