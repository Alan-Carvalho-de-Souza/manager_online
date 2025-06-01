# Arquivo: app/simulacao_automatica.py - VERSÃO CORRIGIDA
import random
from datetime import datetime

def simular_partida_automatica(clube1, clube2):
    """
    Simula uma partida automaticamente sem interface do usuário.
    Retorna um dicionário com os resultados da partida.
    
    Args:
        clube1: Dicionário com dados do time mandante
        clube2: Dicionário com dados do time visitante
    
    Returns:
        dict: Resultado da partida com gols, artilheiros, marcadores, etc.
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
    
    # Simular aproximadamente 2-4 chances de gol por jogo
    num_chances = random.randint(2, 6)
    
    for _ in range(num_chances):
        # Decidir qual time tem a chance
        if random.random() < prob1:
            # Chance para o mandante
            if random.random() < 0.35:  # 35% de chance de converter em gol
                gols1 += 1
        else:
            # Chance para o visitante
            if random.random() < 0.30:  # 30% de chance (visitante tem menos chance)
                gols2 += 1
    
    # Garantir pelo menos alguma variação nos resultados
    if random.random() < 0.15:  # 15% chance de gol extra aleatório
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
            posicao = jogador.get('posicao', 'Meio-campo').lower()
            if 'atacante' in posicao or 'centroavante' in posicao:
                peso = 3  # Atacantes têm 3x mais chance
            elif 'meio' in posicao:
                peso = 2  # Meio-campistas têm 2x mais chance
            else:
                peso = 1  # Defensores e goleiros têm chance normal
            
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
            posicao = jogador.get('posicao', 'Meio-campo').lower()
            if 'atacante' in posicao or 'centroavante' in posicao:
                peso = 3
            elif 'meio' in posicao:
                peso = 2
            else:
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
    Calcula estatísticas agregadas de um time.
    
    Args:
        jogadores: Lista de jogadores do time
    
    Returns:
        dict: Estatísticas do time (habilidade média, etc.)
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
