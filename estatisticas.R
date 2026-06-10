# Carregar os dados do CSV
dados <- read.csv("plantios.csv", stringsAsFactors = FALSE)

# Verificar se os dados foram carregados corretamente
if (nrow(dados) == 0) {
  cat("Nenhum dado encontrado no arquivo CSV.\n")
} else {
  cat("Dados carregados com sucesso!\n\n")
  
  # Mostrar resumo geral
  print(summary(dados))
  
  # Estatísticas por cultura
  culturas <- unique(dados$cultura)
  
  for (cultura in culturas) {
    cat("\n--- Estatísticas para", cultura, "---\n")
    subset <- subset(dados, cultura == cultura)
    
    media_area <- mean(subset$area)
    desvio_area <- sd(subset$area)
    
    media_insumo <- mean(subset$insumo_total)
    desvio_insumo <- sd(subset$insumo_total)
    
    cat(sprintf("Média da área: %.2f m²\n", media_area))
    cat(sprintf("Desvio padrão da área: %.2f m²\n", desvio_area))
    cat(sprintf("Média do insumo total: %.2f L\n", media_insumo))
    cat(sprintf("Desvio padrão do insumo total: %.2f L\n", desvio_insumo))
  }
}
