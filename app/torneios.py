# Arquivo: app/torneios.py
import streamlit as st
import pandas as pd
import random
import time
import json
import os
from datetime import datetime

# Importar a função de simulação do módulo existente
from app.simulacao import simular_partida

class TorneioMataMata:
    def __init__(self, nome, times, formato="ida_volta"):
        self.nome = nome
        self.times = times
        self.formato = formato  # "ida_volta" ou "jogo_unico"
        self.fase_atual = None
        self.chaves = {}
        self.resultados = {}
        self.grupos = {}  # Novo: para armazenar dados dos grupos
        self.classificados_grupos = []  # Novo: times que passaram da fase de grupos
        self.campeao = None
        self.vice = None
        self.historico = []
        
    def validar_numero_times(self):
        """Valida se o número de times é válido para mata-mata"""
        num_times = len(self.times)
        potencias_validas = [2, 4, 8, 16, 32, 64]
        
        if num_times not in potencias_validas:
            return False, f"Número inválido de times ({num_times}). Use: {potencias_validas}"
        
        return True, "OK"
    
    def gerar_fases(self):
        """Gera as fases do torneio baseado no número de times - VERSÃO COM GRUPOS"""
        num_times = len(self.times)
        fases = []
        
        # Lógica para gerar fases incluindo grupos quando necessário
        if num_times == 2:
            fases = ["Final"]
        elif num_times == 4:
            fases = ["Semifinais", "Final"]
        elif num_times == 8:
            fases = ["Quartas de Final", "Semifinais", "Final"]
        elif num_times == 16:
            fases = ["Oitavas de Final", "Quartas de Final", "Semifinais", "Final"]
        elif num_times == 32:
            # Para 32 times: Grupos → Oitavas → Quartas → Semis → Final
            fases = ["Fase de Grupos", "Oitavas de Final", "Quartas de Final", "Semifinais", "Final"]
        elif num_times == 64:
            fases = ["Fase de Grupos", "Fase de 32", "Oitavas de Final", "Quartas de Final", "Semifinais", "Final"]
        else:
            # Fallback para outros números
            times_restantes = num_times
            while times_restantes > 2:
                if times_restantes >= 32:
                    fases.append("Oitavas de Final")
                elif times_restantes >= 16:
                    fases.append("Quartas de Final")
                elif times_restantes >= 8:
                    fases.append("Semifinais")
                elif times_restantes >= 4:
                    fases.append("Semifinais")
                times_restantes = times_restantes // 2
            fases.append("Final")
        
        return fases
    
    def sortear_grupos(self, times_participantes, num_grupos=8):
        """Sorteia os grupos para a fase de grupos"""
        if len(times_participantes) != 32:
            raise ValueError("Fase de grupos requer exatamente 32 times")
        
        # Embaralhar times
        times_embaralhados = times_participantes.copy()
        random.shuffle(times_embaralhados)
        
        grupos = {}
        times_por_grupo = len(times_participantes) // num_grupos
        
        for i in range(num_grupos):
            letra_grupo = chr(65 + i)  # A, B, C, D, E, F, G, H
            inicio = i * times_por_grupo
            fim = inicio + times_por_grupo
            
            grupos[f"Grupo {letra_grupo}"] = {
                'times': times_embaralhados[inicio:fim],
                'jogos': [],
                'tabela': [],
                'classificados': []
            }
        
        return grupos
    
    def simular_grupo(self, nome_grupo, times_grupo):
        """Simula todos os jogos de um grupo e retorna a classificação"""
        jogos = []
        
        # Gerar todos os confrontos do grupo (cada time joga com todos os outros)
        for i in range(len(times_grupo)):
            for j in range(i + 1, len(times_grupo)):
                clube1 = times_grupo[i]
                clube2 = times_grupo[j]
                
                # Simular partida
                gols1, gols2 = simular_partida(clube1, clube2)
                
                jogo = {
                    'time1': clube1,
                    'time2': clube2,
                    'gols1': gols1,
                    'gols2': gols2,
                    'vencedor': clube1 if gols1 > gols2 else clube2 if gols2 > gols1 else None
                }
                jogos.append(jogo)
        
        # Calcular classificação do grupo
        classificacao = {}
        for clube in times_grupo:
            classificacao[clube['nome']] = {
                'time': clube,
                'pontos': 0,
                'jogos': 0,
                'vitorias': 0,
                'empates': 0,
                'derrotas': 0,
                'gols_pro': 0,
                'gols_contra': 0,
                'saldo': 0
            }
        
        # Processar resultados dos jogos
        for jogo in jogos:
            nome1 = jogo['time1']['nome']
            nome2 = jogo['time2']['nome']
            gols1 = jogo['gols1']
            gols2 = jogo['gols2']
            
            # Atualizar estatísticas
            classificacao[nome1]['jogos'] += 1
            classificacao[nome2]['jogos'] += 1
            classificacao[nome1]['gols_pro'] += gols1
            classificacao[nome1]['gols_contra'] += gols2
            classificacao[nome2]['gols_pro'] += gols2
            classificacao[nome2]['gols_contra'] += gols1
            
            if gols1 > gols2:  # Time1 venceu
                classificacao[nome1]['pontos'] += 3
                classificacao[nome1]['vitorias'] += 1
                classificacao[nome2]['derrotas'] += 1
            elif gols2 > gols1:  # Time2 venceu
                classificacao[nome2]['pontos'] += 3
                classificacao[nome2]['vitorias'] += 1
                classificacao[nome1]['derrotas'] += 1
            else:  # Empate
                classificacao[nome1]['pontos'] += 1
                classificacao[nome2]['pontos'] += 1
                classificacao[nome1]['empates'] += 1
                classificacao[nome2]['empates'] += 1
        
        # Calcular saldo de gols
        for stats in classificacao.values():
            stats['saldo'] = stats['gols_pro'] - stats['gols_contra']
        
        # Ordenar por pontos, saldo de gols, gols marcados
        classificacao_ordenada = sorted(
            classificacao.values(),
            key=lambda x: (x['pontos'], x['saldo'], x['gols_pro']),
            reverse=True
        )
        
        # Os 2 primeiros se classificam
        classificados = [classificacao_ordenada[0]['time'], classificacao_ordenada[1]['time']]
        
        return {
            'jogos': jogos,
            'classificacao': classificacao_ordenada,
            'classificados': classificados
        }
    
    def sortear_chaves(self, times_participantes):
        """Sorteia as chaves de uma fase"""
        times_embaralhados = times_participantes.copy()
        random.shuffle(times_embaralhados)
        
        chaves = []
        for i in range(0, len(times_embaralhados), 2):
            chave = {
                'time1': times_embaralhados[i],
                'time2': times_embaralhados[i+1],
                'resultado_ida': None,
                'resultado_volta': None,
                'vencedor': None,
                'detalhes': {}
            }
            chaves.append(chave)
        
        return chaves
    
    def simular_penaltis(self, clube1, clube2):
        """Simula disputa de pênaltis"""
        penaltis1 = 0
        penaltis2 = 0
        rodadas = 0
        max_rodadas = 10
        
        # Simular até 5 cobranças para cada time
        for rodada in range(5):
            if random.random() < 0.75:  # 75% de chance de converter
                penaltis1 += 1
            if random.random() < 0.75:
                penaltis2 += 1
            rodadas += 1
        
        # Se empatado, morte súbita
        while penaltis1 == penaltis2 and rodadas < max_rodadas:
            gol1 = random.random() < 0.75
            gol2 = random.random() < 0.75
            
            if gol1:
                penaltis1 += 1
            if gol2:
                penaltis2 += 1
            
            rodadas += 1
            
            if gol1 and not gol2:
                break
            if gol2 and not gol1:
                break
        
        # Se ainda empatado, sorteio
        if penaltis1 == penaltis2:
            vencedor = random.choice([clube1['nome'], clube2['nome']])
            if vencedor == clube1['nome']:
                penaltis1 += 1
            else:
                penaltis2 += 1
        
        return penaltis1, penaltis2
    
    def determinar_vencedor_chave(self, chave):
        """Determina o vencedor de uma chave baseado no formato"""
        clube1 = chave['time1']
        clube2 = chave['time2']
        
        if self.formato == "jogo_unico":
            gols1, gols2 = chave['resultado_ida']
            
            if gols1 > gols2:
                return clube1, f"{gols1}-{gols2}"
            elif gols2 > gols1:
                return clube2, f"{gols1}-{gols2}"
            else:
                pen1, pen2 = self.simular_penaltis(clube1, clube2)
                if pen1 > pen2:
                    return clube1, f"{gols1}-{gols2} ({pen1}-{pen2} pên.)"
                else:
                    return clube2, f"{gols1}-{gols2} ({pen1}-{pen2} pên.)"
        
        else:  # ida_volta
            gols1_ida, gols2_ida = chave['resultado_ida']
            gols1_volta, gols2_volta = chave['resultado_volta']
            
            total_time1 = gols1_ida + gols1_volta
            total_time2 = gols2_ida + gols2_volta
            
            if total_time1 > total_time2:
                return clube1, f"Agregado: {total_time1}-{total_time2}"
            elif total_time2 > total_time1:
                return clube2, f"Agregado: {total_time1}-{total_time2}"
            else:
                # Verificar gols fora
                gols_fora_time1 = gols1_volta
                gols_fora_time2 = gols2_ida
                
                if gols_fora_time1 > gols_fora_time2:
                    return clube1, f"Agregado: {total_time1}-{total_time2} (gols fora)"
                elif gols_fora_time2 > gols_fora_time1:
                    return clube2, f"Agregado: {total_time1}-{total_time2} (gols fora)"
                else:
                    # Pênaltis
                    pen1, pen2 = self.simular_penaltis(clube1, clube2)
                    if pen1 > pen2:
                        return clube1, f"Agregado: {total_time1}-{total_time2} ({pen1}-{pen2} pên.)"
                    else:
                        return clube2, f"Agregado: {total_time1}-{total_time2} ({pen1}-{pen2} pên.)"

def exibir_grupos(grupos):
    """Exibe os grupos da fase de grupos"""
    st.subheader("🏟️ Fase de Grupos - Sorteio")
    
    # Exibir grupos em colunas
    cols = st.columns(4)  # 4 colunas para mostrar 2 grupos por linha
    
    for i, (nome_grupo, dados_grupo) in enumerate(grupos.items()):
        with cols[i % 4]:
            st.markdown(f"### {nome_grupo}")
            
            for j, clube in enumerate(dados_grupo['times']):
                # Mostrar logo se disponível
                if clube.get('logo_base64'):
                    st.markdown(
                        f"""
                        <div style="display: flex; align-items: center; margin-bottom: 8px;">
                            <img src="data:image/png;base64,{clube['logo_base64']}" 
                                 style="width: 25px; height: 25px; margin-right: 8px;">
                            <span style="font-size: 14px;">{clube['nome']}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.write(f"• {clube['nome']}")
    
    st.markdown("---")

def exibir_resultados_grupo(nome_grupo, resultados_grupo):
    """Exibe os resultados de um grupo"""
    st.subheader(f"📊 {nome_grupo} - Resultados")
    
    # Dividir em duas colunas: jogos e classificação
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### 🏟️ Jogos Realizados")
        for jogo in resultados_grupo['jogos']:
            resultado_texto = f"{jogo['time1']['nome']} {jogo['gols1']} x {jogo['gols2']} {jogo['time2']['nome']}"
            if jogo['vencedor']:
                st.success(f"✅ {resultado_texto}")
            else:
                st.info(f"🔄 {resultado_texto}")
    
    with col2:
        st.markdown("#### 📈 Classificação")
        
        # Cabeçalho da tabela
        st.markdown("""
        | Pos | Time | Pts | J | V | E | D | GP | GC | SG |
        |-----|------|-----|---|---|---|---|----|----|----| 
        """)
        
        # Dados da classificação
        for i, stats in enumerate(resultados_grupo['classificacao']):
            pos = i + 1
            nome = stats['time']['nome']
            pts = stats['pontos']
            j = stats['jogos']
            v = stats['vitorias']
            e = stats['empates']
            d = stats['derrotas']
            gp = stats['gols_pro']
            gc = stats['gols_contra']
            sg = stats['saldo']
            
            # Destacar classificados
            if i < 2:
                classificado = "🟢"  # Verde para classificados
            else:
                classificado = "🔴"  # Vermelho para eliminados
            
            st.markdown(f"| {classificado} {pos}º | {nome} | {pts} | {j} | {v} | {e} | {d} | {gp} | {gc} | {sg} |")
        
        # Legenda
        st.caption("🟢 Classificado para as Oitavas | 🔴 Eliminado")
        
        # Mostrar classificados
        classificados_nomes = [clube['nome'] for clube in resultados_grupo['classificados']]
        st.success(f"🏆 Classificados: {' e '.join(classificados_nomes)}")

def simular_fase_grupos_completa(grupos):
    """Simula toda a fase de grupos"""
    st.subheader("⚽ Simulando Fase de Grupos")
    
    todos_classificados = []
    resultados_todos_grupos = {}
    
    # Simular cada grupo
    for nome_grupo, dados_grupo in grupos.items():
        st.markdown(f"### 🏟️ Simulando {nome_grupo}")
        
        # Criar instância temporária para usar o método simular_grupo
        torneio_temp = TorneioMataMata("temp", [], "ida_volta")
        resultados_grupo = torneio_temp.simular_grupo(nome_grupo, dados_grupo['times'])
        
        # Exibir resultados
        with st.expander(f"📊 Ver detalhes do {nome_grupo}", expanded=False):
            exibir_resultados_grupo(nome_grupo, resultados_grupo)
        
        # Adicionar classificados
        todos_classificados.extend(resultados_grupo['classificados'])
        resultados_todos_grupos[nome_grupo] = resultados_grupo
        
        # Pequena pausa para visualização
        import time as time_module
        time_module.sleep(0.3)
    
    # Resumo final da fase de grupos
    st.success(f"✅ Fase de Grupos Concluída! {len(todos_classificados)} times classificados para as Oitavas de Final")
    
    # Mostrar todos os classificados organizados
    st.markdown("### 🏆 Times Classificados para as Oitavas de Final")
    
    cols = st.columns(4)
    for i, clube in enumerate(todos_classificados):
        with cols[i % 4]:
            if clube.get('logo_base64'):
                st.markdown(
                    f"""
                    <div style="text-align: center; margin-bottom: 10px;">
                        <img src="data:image/png;base64,{clube['logo_base64']}" 
                             style="width: 40px; height: 40px;">
                        <br>
                        <small>{clube['nome']}</small>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(f"**{clube['nome']}**")
    
    return todos_classificados, resultados_todos_grupos

def exibir_chave_torneio(chaves, fase_nome, formato="ida_volta"):
    """Exibe as chaves de uma fase do torneio"""
    st.subheader(f"🏆 {fase_nome}")
    
    for i, chave in enumerate(chaves):
        st.markdown(f"### 🥊 Chave {i+1}: {chave['time1']['nome']} x {chave['time2']['nome']}")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        # Time 1
        with col1:
            if chave['time1'].get('logo_base64'):
                st.markdown(
                    f'<div style="text-align: center"><img src="data:image/png;base64,{chave["time1"]["logo_base64"]}" style="max-width: 60px; max-height: 60px;"></div>',
                    unsafe_allow_html=True
                )
            st.markdown(f"**{chave['time1']['nome']}**")
        
        # Resultados
        with col2:
            if formato == "jogo_unico":
                if chave['resultado_ida']:
                    gols1, gols2 = chave['resultado_ida']
                    st.markdown(f"### 🏟️ {gols1} - {gols2}")
                    
                    if chave['vencedor']:
                        st.success(f"🏆 Vencedor: **{chave['vencedor']['nome']}**")
                        if chave.get('detalhes'):
                            st.info(f"📊 {chave['detalhes']}")
                else:
                    st.markdown("### ⏳ Aguardando...")
            
            else:  # ida_volta
                if chave['resultado_ida']:
                    gols1_ida, gols2_ida = chave['resultado_ida']
                    st.markdown(f"**Ida:** {gols1_ida} - {gols2_ida}")
                else:
                    st.markdown("**Ida:** ⏳ Aguardando...")
                
                if chave['resultado_volta']:
                    gols1_volta, gols2_volta = chave['resultado_volta']
                    st.markdown(f"**Volta:** {gols1_volta} - {gols2_volta}")
                    
                    if chave['resultado_ida'] and chave['resultado_volta']:
                        total1 = gols1_ida + gols1_volta
                        total2 = gols2_ida + gols2_volta
                        st.markdown(f"**Agregado:** {total1} - {total2}")
                        
                        if chave['vencedor']:
                            st.success(f"🏆 Vencedor: **{chave['vencedor']['nome']}**")
                            if chave.get('detalhes'):
                                st.info(f"📊 {chave['detalhes']}")
                else:
                    st.markdown("**Volta:** ⏳ Aguardando...")
        
        # Time 2
        with col3:
            if chave['time2'].get('logo_base64'):
                st.markdown(
                    f'<div style="text-align: center"><img src="data:image/png;base64,{chave["time2"]["logo_base64"]}" style="max-width: 60px; max-height: 60px;"></div>',
                    unsafe_allow_html=True
                )
            st.markdown(f"**{chave['time2']['nome']}**")
        
        st.markdown("---")

def simular_fase_completa(chaves, fase_nome, formato="ida_volta"):
    """Simula uma fase completa do torneio"""
    st.subheader(f"⚽ Simulando {fase_nome}")
    
    vencedores = []
    
    for i, chave in enumerate(chaves):
        st.markdown(f"### 🥊 Chave {i+1}: {chave['time1']['nome']} x {chave['time2']['nome']}")
        
        st.info("📺 Simulando Jogo de Ida...")
        
        # Simular jogo de ida
        gols1_ida, gols2_ida = simular_partida(chave['time1'], chave['time2'])
        chave['resultado_ida'] = (gols1_ida, gols2_ida)
        
        st.success(f"🏟️ Resultado da Ida: {chave['time1']['nome']} {gols1_ida} x {gols2_ida} {chave['time2']['nome']}")
        
        if formato == "ida_volta":
            st.info("📺 Simulando Jogo de Volta...")
            
            # Simular jogo de volta
            gols2_volta, gols1_volta = simular_partida(chave['time2'], chave['time1'])
            chave['resultado_volta'] = (gols1_volta, gols2_volta)
            
            st.success(f"🏟️ Resultado da Volta: {chave['time2']['nome']} {gols2_volta} x {gols1_volta} {chave['time1']['nome']}")
        
        # Determinar vencedor
        torneio_temp = TorneioMataMata("temp", [], formato)
        vencedor, detalhes = torneio_temp.determinar_vencedor_chave(chave)
        
        chave['vencedor'] = vencedor
        chave['detalhes'] = detalhes
        vencedores.append(vencedor)
        
        st.success(f"🏆 **{vencedor['nome']}** avança para a próxima fase!")
        st.info(f"📊 {detalhes}")
        st.markdown("---")
        
        import time as time_module
        time_module.sleep(0.5)
    
    return vencedores

def salvar_historico_torneio(torneio):
    """Salva o histórico do torneio"""
    try:
        # Criar diretório data se não existir
        if not os.path.exists("data"):
            os.makedirs("data")
            st.info("📁 Pasta 'data' criada")
        
        # Criar diretório de torneios
        historico_dir = "data/torneios"
        if not os.path.exists(historico_dir):
            os.makedirs(historico_dir)
            st.info("📁 Pasta 'data/torneios' criada")
        
        arquivo_historico = os.path.join(historico_dir, "historico_torneios.json")
        
        dados_torneio = {
            'nome': torneio.nome,
            'data': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'formato': torneio.formato,
            'campeao': torneio.campeao['nome'] if torneio.campeao else None,
            'vice': torneio.vice['nome'] if torneio.vice else None,
            'num_times': len(torneio.times),
            'times_participantes': [clube['nome'] for clube in torneio.times],
            'teve_grupos': len(torneio.times) == 32  # Novo campo para indicar se teve fase de grupos
        }
        
        # Carregar histórico existente
        historico = []
        if os.path.exists(arquivo_historico):
            try:
                with open(arquivo_historico, 'r', encoding='utf-8') as f:
                    historico = json.load(f)
            except json.JSONDecodeError:
                st.warning("⚠️ Arquivo de histórico corrompido, criando novo")
                historico = []
            except Exception as e:
                st.warning(f"⚠️ Erro ao ler histórico existente: {e}")
                historico = []
        
        # Adicionar novo torneio
        historico.append(dados_torneio)
        
        # Salvar arquivo
        with open(arquivo_historico, 'w', encoding='utf-8') as f:
            json.dump(historico, f, ensure_ascii=False, indent=2)
        
        st.success(f"💾 Histórico salvo com sucesso! Total: {len(historico)} torneios")
        return True
        
    except Exception as e:
        st.error(f"❌ Erro ao salvar histórico: {e}")
        return False

def exibir_historico_torneios():
    """Exibe o histórico de torneios realizados"""
    st.subheader("📊 Histórico de Torneios")
    
    arquivo_historico = "data/torneios/historico_torneios.json"
    
    if not os.path.exists(arquivo_historico):
        st.info("📝 Nenhum torneio realizado ainda.")
        return
    
    try:
        with open(arquivo_historico, 'r', encoding='utf-8') as f:
            historico = json.load(f)
        
        if not historico:
            st.info("📝 Nenhum torneio registrado no histórico.")
            return
        
        # Ordenar por data (mais recente primeiro)
        historico_ordenado = sorted(historico, key=lambda x: x.get('data', ''), reverse=True)
        
        # Estatísticas gerais
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("🏆 Torneios Realizados", len(historico))
        
        with col2:
            campeoes = [t.get('campeao') for t in historico if t.get('campeao')]
            if campeoes:
                campeao_mais_vitorioso = max(set(campeoes), key=campeoes.count)
                vitorias = campeoes.count(campeao_mais_vitorioso)
                st.metric("👑 Maior Campeão", f"{campeao_mais_vitorioso} ({vitorias}x)")
            else:
                st.metric("👑 Maior Campeão", "N/A")
        
        with col3:
            formatos = [t.get('formato', 'N/A') for t in historico]
            if formatos:
                formato_popular = max(set(formatos), key=formatos.count)
                formato_texto = "Ida e Volta" if formato_popular == "ida_volta" else "Jogo Único" if formato_popular == "jogo_unico" else formato_popular
                st.metric("⚽ Formato Popular", formato_texto)
            else:
                st.metric("⚽ Formato Popular", "N/A")
        
        st.markdown("---")
        
        # Lista de torneios
        for i, torneio in enumerate(historico_ordenado):
            teve_grupos = torneio.get('teve_grupos', False)
            icone_grupos = " 🏟️" if teve_grupos else ""
            
            st.markdown(f"### 🏆 {torneio.get('nome', 'Torneio')}{icone_grupos} ({torneio.get('data', 'N/A')[:10]})")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**🏆 Campeão:** {torneio.get('campeao', 'N/A')}")
                st.write(f"**🥈 Vice:** {torneio.get('vice', 'N/A')}")
                formato_texto = "Ida e Volta" if torneio.get('formato') == "ida_volta" else "Jogo Único" if torneio.get('formato') == "jogo_unico" else "N/A"
                st.write(f"**⚽ Formato:** {formato_texto}")
            
            with col2:
                st.write(f"**👥 Times:** {torneio.get('num_times', 'N/A')}")
                st.write(f"**📅 Data:** {torneio.get('data', 'N/A')}")
                if teve_grupos:
                    st.write("**🏟️ Formato:** Com Fase de Grupos")
            
            st.write("**🏟️ Times Participantes:**")
            participantes = torneio.get('times_participantes', [])
            if participantes:
                times_texto = ", ".join(participantes)
                st.write(times_texto)
            else:
                st.write("N/A")
            
            st.markdown("---")
    
    except Exception as e:
        st.error(f"❌ Erro ao carregar histórico: {e}")

def pagina_torneios(clubes):
    """Página principal dos torneios"""
    st.header("🏆 Torneios Mata-Mata")
    
    if not clubes:
        st.error("❌ Nenhum clube carregado. Verifique os arquivos de dados.")
        return
    
    # Sub-abas para organizar melhor
    subtab1, subtab2, subtab3 = st.tabs(["🚀 Novo Torneio", "📊 Histórico", "ℹ️ Sobre"])
    
    with subtab1:
        st.subheader("🎯 Configurar Novo Torneio")
        
        # Nome do torneio
        nome_torneio = st.text_input("📝 Nome do Torneio", value="Champions League 2024")
        
        # Configurações em colunas
        col1, col2 = st.columns(2)
        
        with col1:
            formato = st.selectbox("⚽ Formato dos Jogos", 
                                  ["ida_volta", "jogo_unico"],
                                  format_func=lambda x: "Ida e Volta" if x == "ida_volta" else "Jogo Único")
        
        with col2:
            opcoes_times = [4, 8, 16, 32]
            num_times = st.selectbox("👥 Número de Times", opcoes_times)
            
            # Avisar sobre fase de grupos para 32 times
            if num_times == 32:
                st.info("🏟️ Com 32 times, o torneio terá Fase de Grupos (8 grupos de 4 times)")
        
        if len(clubes) < num_times:
            st.error(f"❌ Você precisa ter pelo menos {num_times} times cadastrados. Atualmente tem {len(clubes)}.")
            return
        
        # Seleção de times
        st.subheader("🎯 Seleção de Times")
        
        metodo_selecao = st.radio("Como selecionar os times?", 
                                 ["Automático (Melhores)", "Manual", "Sorteio"],
                                 horizontal=True)
        
        times_selecionados = []
        
        if metodo_selecao == "Automático (Melhores)":
            times_ordenados = sorted(clubes.values(), 
                                   key=lambda x: x['forca_geral'], reverse=True)
            times_selecionados = times_ordenados[:num_times]
            
            st.write("**Times Selecionados (por força):**")
            for i, clube in enumerate(times_selecionados):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"{i+1}. {clube['nome']}")
                with col2:
                    st.write(f"Força: {clube['forca_geral']}")
        
        elif metodo_selecao == "Manual":
            nomes_clubes = [clube['nome'] for clube in clubes.values()]
            times_escolhidos = st.multiselect(f"Escolha {num_times} times:", 
                                            nomes_clubes, max_selections=num_times)
            
            if len(times_escolhidos) == num_times:
                times_selecionados = [clube for clube in clubes.values() 
                                    if clube['nome'] in times_escolhidos]
                st.success(f"✅ {num_times} times selecionados!")
            else:
                st.warning(f"⚠️ Selecione exatamente {num_times} times. Selecionados: {len(times_escolhidos)}")
        
        else:  # Sorteio
            if st.button("🎲 Sortear Times"):
                times_sorteados = random.sample(list(clubes.values()), num_times)
                times_selecionados = times_sorteados
                st.session_state.times_sorteados = times_selecionados
                st.rerun()
            
            if 'times_sorteados' in st.session_state:
                times_selecionados = st.session_state.times_sorteados
                st.write("**Times Sorteados:**")
                for i, clube in enumerate(times_selecionados):
                    st.write(f"{i+1}. {clube['nome']}")
        
        # Criar torneio se tudo estiver pronto
        if len(times_selecionados) == num_times:
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("🚀 Criar e Simular Torneio", use_container_width=True, type="primary"):
                    torneio = TorneioMataMata(nome_torneio, times_selecionados, formato)
                    valido, erro = torneio.validar_numero_times()
                    
                    if valido:
                        st.success(f"✅ Torneio '{nome_torneio}' criado com sucesso!")
                        # Reset completo do estado
                        st.session_state.torneio_atual = torneio
                        st.session_state.fase_atual_idx = 0
                        st.session_state.times_atuais = times_selecionados.copy()
                        st.session_state.fases_completadas = []
                        st.session_state.fase_grupos_concluida = False
                        if 'times_sorteados' in st.session_state:
                            del st.session_state.times_sorteados
                        st.rerun()
                    else:
                        st.error(f"❌ {erro}")
        
        # Simular torneio se criado
        if 'torneio_atual' in st.session_state:
            st.markdown("---")
            simular_torneio_completo(st.session_state.torneio_atual)
    
    with subtab2:
        exibir_historico_torneios()
    
    with subtab3:
        st.subheader("ℹ️ Como Funciona o Sistema de Torneios")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🏆 Tipos de Torneio Suportados:**
            - Champions League (16/32 times)
            - Copa do Mundo (32 times)
            - Copa do Brasil (variável)
            - Torneios personalizados
            
            **⚙️ Configurações:**
            - Formato: Ida e Volta ou Jogo Único
            - Times: 4, 8, 16 ou 32 participantes
            - Seleção: Automática, Manual ou Sorteio
            - **NOVO:** Fase de Grupos automática para 32 times
            
            **🎯 Critérios de Desempate:**
            - Grupos: Pontos → Saldo → Gols marcados
            - Mata-mata: Ida e Volta → Gols fora → Pênaltis
            - Jogo Único: Pênaltis direto
            """)
        
        with col2:
            st.markdown("""
            **🎮 Como Usar:**
            1. Configure o nome do torneio
            2. Escolha o formato (ida/volta ou único)
            3. Defina quantos times participarão
            4. **Para 32 times:** Fase de grupos automática
            5. Selecione os times participantes
            6. Clique em "Criar e Simular Torneio"
            7. Acompanhe fase por fase até a final!
            
            **💾 Recursos:**
            - **NOVO:** Sistema completo de grupos
            - Histórico automático de torneios
            - Estatísticas de campeões
            - Sistema de pênaltis realístico
            - Animações das partidas
            """)
        
        st.markdown("---")
        
        # Nova seção explicando a fase de grupos
        st.subheader("🏟️ Fase de Grupos (32 times)")
        st.markdown("""
        **Como funciona:**
        - 32 times são divididos em 8 grupos (A, B, C, D, E, F, G, H)
        - Cada grupo tem 4 times
        - Todos se enfrentam dentro do grupo (3 jogos por time)
        - Os 2 melhores de cada grupo se classificam (16 times)
        - Critério: Pontos → Saldo de gols → Gols marcados
        - Segue para as Oitavas de Final com 16 times
        """)
        
        st.info("💡 **Dica:** Use a seleção automática para pegar os times mais fortes, ou faça um sorteio para mais surpresas!")

def simular_torneio_completo(torneio):
    """Simula um torneio completo do início ao fim - VERSÃO COM GRUPOS"""
    st.subheader(f"🏆 {torneio.nome}")
    
    # Informações do torneio
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("👥 Times", len(torneio.times))
    with col2:
        st.metric("⚽ Formato", "Ida e Volta" if torneio.formato == "ida_volta" else "Jogo Único")
    with col3:
        tem_grupos = len(torneio.times) == 32
        if tem_grupos:
            total_jogos = 48 + 15  # 48 jogos nos grupos + 15 no mata-mata
        else:
            total_jogos = len(torneio.times) - 1 if torneio.formato == "jogo_unico" else (len(torneio.times) - 1) * 2
        st.metric("🏟️ Total de Jogos", total_jogos)
    
    # Gerar fases
    fases = torneio.gerar_fases()
    st.write(f"**📋 Fases do Torneio:** {' → '.join(fases)}")
    
    # Inicializar estados se necessário
    if 'fase_atual_idx' not in st.session_state:
        st.session_state.fase_atual_idx = 0
    
    if 'times_atuais' not in st.session_state:
        st.session_state.times_atuais = torneio.times.copy()
    
    if 'fases_completadas' not in st.session_state:
        st.session_state.fases_completadas = []
    
    if 'fase_grupos_concluida' not in st.session_state:
        st.session_state.fase_grupos_concluida = False
    
    # Verificar se torneio já foi concluído
    if st.session_state.fase_atual_idx >= len(fases):
        st.success("🏆 **TORNEIO CONCLUÍDO!**")
        
        if torneio.campeao:
            st.balloons()
            st.success(f"🏆 **CAMPEÃO: {torneio.campeao['nome']}** 🏆")
            if torneio.vice:
                st.info(f"🥈 **Vice-campeão:** {torneio.vice['nome']}")
        
        if st.button("🎉 Novo Torneio"):
            # Limpar todos os estados
            keys_to_delete = ['torneio_atual', 'fase_atual_idx', 'times_atuais', 'fases_completadas', 'fase_grupos_concluida']
            for key in keys_to_delete:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        return torneio
    
    # Mostrar fases anteriores (já completadas)
    for i, fase in enumerate(fases):
        if i < st.session_state.fase_atual_idx:
            st.subheader(f"✅ {fase} (Concluída)")
            if i < len(st.session_state.fases_completadas):
                fase_info = st.session_state.fases_completadas[i]
                if fase == "Fase de Grupos":
                    st.success(f"🏆 {len(fase_info.get('classificados', []))} times classificados para as Oitavas")
                else:
                    if 'vencedores' in fase_info:
                        vencedores_nomes = [v['nome'] for v in fase_info['vencedores']]
                        st.success(f"🏆 Classificados: {', '.join(vencedores_nomes)}")
    
    # Mostrar fase atual
    if st.session_state.fase_atual_idx < len(fases):
        fase_atual = fases[st.session_state.fase_atual_idx]
        
        st.markdown("---")
        st.subheader(f"🎯 FASE ATUAL: {fase_atual}")
        
        # LÓGICA ESPECIAL PARA FASE DE GRUPOS
        if fase_atual == "Fase de Grupos":
            if not st.session_state.fase_grupos_concluida:
                # Sortear grupos
                grupos = torneio.sortear_grupos(st.session_state.times_atuais)
                torneio.grupos = grupos
                
                # Exibir sorteio dos grupos
                exibir_grupos(grupos)
                
                # Botão para simular fase de grupos
                col1, col2, col3 = st.columns([1, 1, 1])
                with col2:
                    if st.button("⚽ Simular Fase de Grupos", use_container_width=True, type="primary"):
                        # Simular todos os grupos
                        classificados, resultados_grupos = simular_fase_grupos_completa(grupos)
                        
                        # Salvar resultados
                        torneio.classificados_grupos = classificados
                        torneio.resultados = {"Fase de Grupos": resultados_grupos}
                        
                        # Atualizar estados
                        st.session_state.times_atuais = classificados
                        st.session_state.fase_grupos_concluida = True
                        st.session_state.fase_atual_idx += 1
                        
                        # Salvar na lista de fases completadas
                        fase_info = {
                            'nome': fase_atual,
                            'grupos': grupos,
                            'classificados': classificados,
                            'resultados': resultados_grupos
                        }
                        st.session_state.fases_completadas.append(fase_info)
                        
                        st.rerun()
            else:
                st.success("✅ Fase de Grupos já foi concluída!")
        
        # LÓGICA PARA FASES MATA-MATA
        else:
            # Verificar se temos times suficientes para a fase
            if len(st.session_state.times_atuais) < 2:
                st.error("❌ Erro: Não há times suficientes para continuar o torneio!")
                return torneio
            
            # Sortear chaves para a fase atual
            chaves = torneio.sortear_chaves(st.session_state.times_atuais)
            
            # Exibir chaves
            st.subheader(f"🎲 Sorteio - {fase_atual}")
            exibir_chave_torneio(chaves, f"Chaves - {fase_atual}", torneio.formato)
            
            # Botão para simular a fase
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button(f"⚽ Simular {fase_atual}", key=f"simular_{fase_atual}_{st.session_state.fase_atual_idx}", use_container_width=True, type="primary"):
                    # Simular a fase
                    vencedores = simular_fase_completa(chaves, fase_atual, torneio.formato)
                    
                    # Salvar informações da fase
                    torneio.chaves[fase_atual] = chaves
                    torneio.resultados[fase_atual] = vencedores
                    
                    # Salvar na lista de fases completadas
                    fase_info = {
                        'nome': fase_atual,
                        'chaves': chaves,
                        'vencedores': vencedores
                    }
                    st.session_state.fases_completadas.append(fase_info)
                    
                    st.success(f"✅ {fase_atual} concluída!")
                    st.info(f"🏆 Classificados para próxima fase: {[v['nome'] for v in vencedores]}")
                    
                    # Verificar se é a final
                    if fase_atual == "Final":
                        if len(vencedores) == 1:
                            # Definir campeão
                            torneio.campeao = vencedores[0]
                            
                            # Encontrar vice-campeão
                            for chave in chaves:
                                if chave['vencedor'] == torneio.campeao:
                                    torneio.vice = chave['time1'] if chave['time2'] == torneio.campeao else chave['time2']
                                    break
                            
                            # Salvar histórico
                            sucesso_save = salvar_historico_torneio(torneio)
                            
                            # Marcar torneio como concluído
                            st.session_state.fase_atual_idx = len(fases)  # Marca como concluído
                            
                            st.rerun()
                        else:
                            st.error("❌ Erro: Final deveria ter apenas 1 vencedor!")
                    else:
                        # Avançar para próxima fase
                        st.session_state.times_atuais = vencedores
                        st.session_state.fase_atual_idx += 1
                        st.rerun()
    
    # Mostrar fases futuras
    for i, fase in enumerate(fases):
        if i > st.session_state.fase_atual_idx:
            st.subheader(f"⏳ {fase} (Aguardando)")
            st.info("Esta fase será desbloqueada após a conclusão da fase anterior.")
    
    return torneio

def exibir_classificacao_geral_torneios(clubes):
    """
    Exibe a classificação geral dos times nos torneios - Hall da Fama
    VERSÃO CORRIGIDA com tratamento de arquivos vazios/corrompidos
    """
    st.header("👑 Hall da Fama dos Torneios")
    
    arquivo_historico = "data/torneios/historico_torneios.json"
    
    # Verificar se arquivo existe
    if not os.path.exists(arquivo_historico):
        st.info("📝 Nenhum torneio realizado ainda. Vá para a aba 'Torneios' para criar o primeiro!")
        
        # Mostrar exemplo de como ficará
        st.subheader("🎯 Como Funcionará")
        st.markdown("""
        Quando você realizar torneios, esta aba mostrará:
        - 🏆 **Ranking de Campeões** - Times que mais venceram torneios
        - 🥈 **Ranking de Vice-Campeões** - Times que mais chegaram à final
        - 📊 **Estatísticas Gerais** - Performance geral de cada time
        - 🏟️ **Participações** - Quantos torneios cada time participou
        - 📈 **Taxa de Sucesso** - Porcentagem de títulos por participação
        """)
        return
    
    # Verificar se arquivo não está vazio
    try:
        tamanho_arquivo = os.path.getsize(arquivo_historico)
        
        if tamanho_arquivo == 0:
            st.warning("⚠️ Arquivo de histórico está vazio. Realize alguns torneios primeiro!")
            return
            
    except Exception as e:
        st.error(f"❌ Erro ao verificar arquivo: {e}")
        return
    
    try:
        # Tentar ler o arquivo
        with open(arquivo_historico, 'r', encoding='utf-8') as f:
            conteudo = f.read().strip()
            
        # Verificar se conteúdo não está vazio
        if not conteudo:
            st.warning("⚠️ Arquivo de histórico está vazio. Realize alguns torneios primeiro!")
            return
        
        # Tentar fazer parse do JSON
        try:
            historico_torneios = json.loads(conteudo)
        except json.JSONDecodeError as e:
            st.error(f"❌ Erro no formato JSON: {e}")
            
            # Opção para recriar arquivo
            if st.button("🔧 Recriar Arquivo de Histórico"):
                try:
                    # Criar backup
                    backup_file = arquivo_historico + '.backup'
                    with open(backup_file, 'w') as f:
                        f.write(conteudo)
                    
                    # Criar arquivo novo e vazio
                    with open(arquivo_historico, 'w', encoding='utf-8') as f:
                        json.dump([], f, ensure_ascii=False, indent=2)
                    
                    st.success("✅ Arquivo recriado! Backup salvo como .backup")
                    st.info("Realize novos torneios para popular o histórico.")
                    st.rerun()
                except Exception as e2:
                    st.error(f"❌ Erro ao recriar arquivo: {e2}")
            return
        
        if not historico_torneios:
            st.info("📝 Nenhum torneio registrado ainda no histórico. Realize alguns torneios primeiro!")
            return
        
        st.success(f"✅ Carregados {len(historico_torneios)} torneios do histórico")
        
        # Processar dados dos torneios
        campeoes_count = {}
        vice_campeoes_count = {}
        participacoes_count = {}
        times_todos = set()
        
        for i, torneio in enumerate(historico_torneios):
            try:
                campeao = torneio.get('campeao')
                vice = torneio.get('vice')
                participantes = torneio.get('times_participantes', [])
                
                # Contar campeões
                if campeao:
                    times_todos.add(campeao)
                    campeoes_count[campeao] = campeoes_count.get(campeao, 0) + 1
                
                # Contar vice-campeões
                if vice:
                    times_todos.add(vice)
                    vice_campeoes_count[vice] = vice_campeoes_count.get(vice, 0) + 1
                
                # Contar participações
                for time in participantes:
                    times_todos.add(time)
                    participacoes_count[time] = participacoes_count.get(time, 0) + 1
                    
            except Exception as e:
                st.warning(f"⚠️ Erro ao processar torneio {i+1}: {e}")
                continue
        
        # Verificar se temos dados processados
        if not times_todos:
            st.warning("⚠️ Nenhum dado válido encontrado nos torneios. Verifique o formato dos dados.")
            return
        
        # Estatísticas gerais no topo
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🏆 Total de Torneios", len(historico_torneios))
        
        with col2:
            st.metric("🏟️ Times Participantes", len(times_todos))
        
        with col3:
            if campeoes_count:
                time_mais_vitorioso = max(campeoes_count.items(), key=lambda x: x[1])
                st.metric("👑 Time Mais Vitorioso", f"{time_mais_vitorioso[0]} ({time_mais_vitorioso[1]}x)")
            else:
                st.metric("👑 Time Mais Vitorioso", "N/A")
        
        with col4:
            total_participacoes = sum(participacoes_count.values())
            st.metric("📊 Total de Participações", total_participacoes)
        
        st.markdown("---")
        
        # Criar abas para diferentes visualizações
        subtab1, subtab2, subtab3, subtab4 = st.tabs([
            "🏆 Ranking de Campeões", 
            "🥈 Ranking de Vice-Campeões", 
            "📊 Classificação Geral",
            "📈 Estatísticas Detalhadas"
        ])
        
        # ABA 1: RANKING DE CAMPEÕES
        with subtab1:
            st.subheader("🏆 Ranking de Campeões")
            
            if not campeoes_count:
                st.info("📝 Nenhum campeão registrado ainda.")
            else:
                # Ordenar por número de títulos
                campeoes_ordenados = sorted(campeoes_count.items(), key=lambda x: x[1], reverse=True)
                
                for i, (time_nome, titulos) in enumerate(campeoes_ordenados):
                    # Encontrar dados do clube para pegar o logo
                    clube_data = None
                    for clube in clubes.values():
                        if clube['nome'] == time_nome:
                            clube_data = clube
                            break
                    
                    # Criar layout para cada campeão
                    col1, col2, col3 = st.columns([1, 4, 1])
                    
                    with col1:
                        # Posição
                        if i == 0:
                            st.markdown("### 🥇")
                        elif i == 1:
                            st.markdown("### 🥈")
                        elif i == 2:
                            st.markdown("### 🥉")
                        else:
                            st.markdown(f"### {i+1}º")
                    
                    with col2:
                        # Logo e nome do time
                        if clube_data and clube_data.get('logo_base64'):
                            st.markdown(
                                f"""
                                <div style="display: flex; align-items: center;">
                                    <img src="data:image/png;base64,{clube_data['logo_base64']}" 
                                         style="width: 40px; height: 40px; margin-right: 15px;">
                                    <div>
                                        <h4 style="margin: 0;">{time_nome}</h4>
                                        <p style="margin: 0; color: #666;">
                                            Participações: {participacoes_count.get(time_nome, 0)} | 
                                            Taxa de Sucesso: {(titulos/participacoes_count.get(time_nome, 1)*100):.1f}%
                                        </p>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        else:
                            st.markdown(f"**{time_nome}**")
                            st.caption(f"Participações: {participacoes_count.get(time_nome, 0)} | Taxa de Sucesso: {(titulos/participacoes_count.get(time_nome, 1)*100):.1f}%")
                    
                    with col3:
                        # Número de títulos
                        st.markdown(f"### {titulos} 🏆")
                    
                    st.markdown("---")
        
        # ABA 2: RANKING DE VICE-CAMPEÕES
        with subtab2:
            st.subheader("🥈 Ranking de Vice-Campeões")
            
            if not vice_campeoes_count:
                st.info("📝 Nenhum vice-campeão registrado ainda.")
            else:
                # Ordenar por número de vice-campeonatos
                vices_ordenados = sorted(vice_campeoes_count.items(), key=lambda x: x[1], reverse=True)
                
                for i, (time_nome, vices) in enumerate(vices_ordenados):
                    # Encontrar dados do clube
                    clube_data = None
                    for clube in clubes.values():
                        if clube['nome'] == time_nome:
                            clube_data = clube
                            break
                    
                    col1, col2, col3 = st.columns([1, 4, 1])
                    
                    with col1:
                        st.markdown(f"### {i+1}º")
                    
                    with col2:
                        if clube_data and clube_data.get('logo_base64'):
                            st.markdown(
                                f"""
                                <div style="display: flex; align-items: center;">
                                    <img src="data:image/png;base64,{clube_data['logo_base64']}" 
                                         style="width: 40px; height: 40px; margin-right: 15px;">
                                    <div>
                                        <h4 style="margin: 0;">{time_nome}</h4>
                                        <p style="margin: 0; color: #666;">
                                            Finais Disputadas: {campeoes_count.get(time_nome, 0) + vices} | 
                                            Títulos: {campeoes_count.get(time_nome, 0)}
                                        </p>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        else:
                            st.markdown(f"**{time_nome}**")
                            st.caption(f"Finais: {campeoes_count.get(time_nome, 0) + vices} | Títulos: {campeoes_count.get(time_nome, 0)}")
                    
                    with col3:
                        st.markdown(f"### {vices} 🥈")
                    
                    st.markdown("---")
        
        # ABA 3: CLASSIFICAÇÃO GERAL
        with subtab3:
            st.subheader("📊 Classificação Geral dos Times")
            
            # Criar DataFrame com todas as estatísticas
            dados_completos = []
            
            for time_nome in times_todos:
                titulos = campeoes_count.get(time_nome, 0)
                vices = vice_campeoes_count.get(time_nome, 0)
                participacoes = participacoes_count.get(time_nome, 0)
                finais = titulos + vices
                taxa_sucesso = (titulos / participacoes * 100) if participacoes > 0 else 0
                taxa_finais = (finais / participacoes * 100) if participacoes > 0 else 0
                pontos = titulos * 3 + vices * 1  # Sistema de pontuação
                
                dados_completos.append({
                    'Time': time_nome,
                    'Títulos': titulos,
                    'Vice': vices,
                    'Finais': finais,
                    'Participações': participacoes,
                    'Taxa Sucesso (%)': round(taxa_sucesso, 1),
                    'Taxa Finais (%)': round(taxa_finais, 1),
                    'Pontos': pontos
                })
            
            # Ordenar por pontos (títulos valem mais)
            dados_completos.sort(key=lambda x: (x['Pontos'], x['Títulos'], x['Finais']), reverse=True)
            
            # Exibir tabela formatada
            for i, dados in enumerate(dados_completos):
                col1, col2, col3, col4, col5, col6 = st.columns([1, 3, 1, 1, 1, 2])
                
                with col1:
                    # Posição com medalha para top 3
                    if i == 0:
                        st.markdown("### 🥇")
                    elif i == 1:
                        st.markdown("### 🥈")
                    elif i == 2:
                        st.markdown("### 🥉")
                    else:
                        st.markdown(f"### {i+1}º")
                
                with col2:
                    # Nome do time com logo
                    clube_data = None
                    for clube in clubes.values():
                        if clube['nome'] == dados['Time']:
                            clube_data = clube
                            break
                    
                    if clube_data and clube_data.get('logo_base64'):
                        st.markdown(
                            f"""
                            <div style="display: flex; align-items: center;">
                                <img src="data:image/png;base64,{clube_data['logo_base64']}" 
                                     style="width: 30px; height: 30px; margin-right: 10px;">
                                <strong>{dados['Time']}</strong>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(f"**{dados['Time']}**")
                
                with col3:
                    st.markdown(f"🏆 **{dados['Títulos']}**")
                
                with col4:
                    st.markdown(f"🥈 **{dados['Vice']}**")
                
                with col5:
                    st.markdown(f"📊 **{dados['Participações']}**")
                
                with col6:
                    st.markdown(f"📈 **{dados['Taxa Sucesso (%)']}%**")
                
                st.markdown("---")
        
        # ABA 4: ESTATÍSTICAS DETALHADAS
        with subtab4:
            st.subheader("📈 Estatísticas Detalhadas")
            
            # Estatísticas por formato de torneio
            formatos_stats = {}
            grupos_stats = {'com_grupos': 0, 'sem_grupos': 0}
            
            for torneio in historico_torneios:
                formato = torneio.get('formato', 'N/A')
                teve_grupos = torneio.get('teve_grupos', False)
                
                if formato not in formatos_stats:
                    formatos_stats[formato] = {'count': 0, 'campeoes': []}
                formatos_stats[formato]['count'] += 1
                if torneio.get('campeao'):
                    formatos_stats[formato]['campeoes'].append(torneio['campeao'])
                
                # Contar torneios com grupos
                if teve_grupos:
                    grupos_stats['com_grupos'] += 1
                else:
                    grupos_stats['sem_grupos'] += 1
            
            st.subheader("⚽ Estatísticas por Formato")
            for formato, stats in formatos_stats.items():
                formato_nome = "Ida e Volta" if formato == "ida_volta" else "Jogo Único" if formato == "jogo_unico" else formato
                st.write(f"**{formato_nome}:** {stats['count']} torneios")
                
                if stats['campeoes']:
                    campeao_formato = max(set(stats['campeoes']), key=stats['campeoes'].count)
                    vitorias_formato = stats['campeoes'].count(campeao_formato)
                    st.write(f"  👑 Maior campeão: {campeao_formato} ({vitorias_formato}x)")
            
            # Estatísticas de grupos
            st.markdown("---")
            st.subheader("🏟️ Estatísticas de Fase de Grupos")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Com Grupos", grupos_stats['com_grupos'])
            with col2:
                st.metric("Sem Grupos", grupos_stats['sem_grupos'])
            
            st.markdown("---")
            
            # Estatísticas por número de times
            st.subheader("👥 Estatísticas por Número de Times")
            tamanhos_stats = {}
            for torneio in historico_torneios:
                num_times = torneio.get('num_times', 0)
                if num_times not in tamanhos_stats:
                    tamanhos_stats[num_times] = {'count': 0, 'campeoes': []}
                tamanhos_stats[num_times]['count'] += 1
                if torneio.get('campeao'):
                    tamanhos_stats[num_times]['campeoes'].append(torneio['campeao'])
            
            for num_times, stats in sorted(tamanhos_stats.items()):
                grupos_text = " (com grupos)" if num_times == 32 else ""
                st.write(f"**{num_times} times{grupos_text}:** {stats['count']} torneios")
                if stats['campeoes']:
                    campeao_tamanho = max(set(stats['campeoes']), key=stats['campeoes'].count)
                    vitorias_tamanho = stats['campeoes'].count(campeao_tamanho)
                    st.write(f"  👑 Maior campeão: {campeao_tamanho} ({vitorias_tamanho}x)")
            
            st.markdown("---")
            
            # Últimos torneios
            st.subheader("🕒 Últimos Torneios Realizados")
            ultimos_torneios = sorted(historico_torneios, key=lambda x: x.get('data', ''), reverse=True)[:5]
            
            for torneio in ultimos_torneios:
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    grupos_icon = " 🏟️" if torneio.get('teve_grupos') else ""
                    st.write(f"**{torneio.get('nome', 'Torneio')}{grupos_icon}**")
                    st.caption(f"📅 {torneio.get('data', 'N/A')[:10]}")
                
                with col2:
                    st.write(f"🏆 {torneio.get('campeao', 'N/A')}")
                
                with col3:
                    st.write(f"🥈 {torneio.get('vice', 'N/A')}")
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados dos torneios: {e}")
        st.error(f"Tipo do erro: {type(e).__name__}")
        
        # Opção para limpar/recriar arquivo
        if st.button("🔧 Recriar Arquivo de Histórico Limpo"):
            try:
                with open(arquivo_historico, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
                st.success("✅ Arquivo de histórico recriado como lista vazia")
                st.info("Agora você pode realizar novos torneios!")
                st.rerun()
            except Exception as e2:
                st.error(f"❌ Erro ao recriar arquivo: {e2}")
