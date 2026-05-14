# Relatório de Desenvolvimento - Ortho-Check

Este documento consolida o histórico de desenvolvimento do projeto Ortho-Check, focado na fiscalização de obras rodoviárias assistida por Inteligência Artificial e Geoprocessamento.

## 📅 Histórico de Iterações

### 🟢 27 de Abril de 2026: Fundação do MVP e Interface Visual
**Foco:** Criação da interface de upload e editor de polígonos.
- **Frontend (React + Vite):** Implementação de design system premium (Glassmorphism) e lógica de upload de imagens (Referência vs. Atual).
- **Editor de Imagem (Three.js):** Integração de ferramenta de desenho de polígonos sobre as imagens para delimitar Áreas de Interesse (ROI).
- **IA (OpenAI):** Configuração de pipeline para envio de imagens com metadados visuais para geração de laudos automáticos.
- **Refinamentos:** Ajuste de aspect ratio no canvas e fechamento automático de polígonos.

### 🔵 30 de Abril de 2026: Backend Espacial e Persistência (Java/Spring)
**Foco:** Estruturação do servidor "Analyzer" para armazenamento georreferenciado.
- **Modelagem de Dados:** Criação da entidade `AuditArea` utilizando **Hibernate Spatial** e **JTS (Java Topology Suite)** para manipulação de polígonos geográficos.
- **Infraestrutura REST:**
  - Desenvolvimento de **Service** com lógica de normalização de SRID (4326) e cálculo de área aproximada em m².
  - Implementação de **Controller** com endpoints para registrar (`POST`) e listar (`GET`) geometrias.
  - Criação de DTOs para isolamento da camada de API.
- **Configuração de Ambiente:**
  - Setup do `application.properties` para conexão com **PostgreSQL/PostGIS**.
  - Configuração do Jackson para serialização automática de GeoJSON.
- **Resolução de Dependências:**
  - Migração para **Spring AI BOM 2.0.0-M5**.
  - Correção de conflitos de versões e configuração do repositório Spring Milestones no `pom.xml`.
  - Validação completa da build via Maven.

### 🟡 07 de Maio de 2026: Testes de Precisão da IA
**Foco:** Experimentação com comparativos visuais.
- **Teste de Avanço:** Avaliação da capacidade da IA em identificar alterações entre duas imagens usando marcadores visuais (quadrados amarelos) para simular avanço de obra.
- **Resultado:** Observou-se a necessidade de maior densidade de dados para evitar respostas genéricas.

---

## 🛠️ Stack Tecnológica Atualizada

| Camada | Tecnologia |
|--------|------------|
| **Backend** | Java 21, Spring Boot 4, Hibernate Spatial, Spring AI |
| **Banco de Dados** | PostgreSQL 17 + PostGIS 3.5 |
| **Frontend** | React, Vite, Three.js (@react-three/fiber) |
| **IA** | OpenAI GPT-4o (Vision) |
| **Formatos** | GeoJSON, WKT, JTS Geometry |

---

## 🚀 Próximos Passos
1. Integração do Frontend com o novo Backend Java para persistência real das áreas desenhadas.
2. Implementação de visualização de mapas (Leaflet/Mapbox) consumindo as áreas do banco.
3. Refinamento dos prompts de IA para incluir cálculos baseados na área em m² calculada pelo backend.

---
*Relatório gerado em 11 de Maio de 2026.*
