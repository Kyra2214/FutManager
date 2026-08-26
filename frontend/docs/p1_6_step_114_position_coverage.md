# P1-6 / passo 114 — Cobertura adequada por posição

Foi adicionado `SportStateStore.position_coverage_alerts(club_id, minimum_available)`. O método deriva alertas do relatório de profundidade, com limiar configurável, posição canônica, atletas disponíveis e IDs relacionados.

O resultado não é persistido: posições abaixo do limiar são sinalizadas em memória a partir do GameState atual. Limiar negativo é rejeitado com erro determinístico. O teste temporário cobre posição descoberta, posição coberta e configuração inválida.
