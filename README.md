<!-- 
  Salesforce Aura Pentest Toolkit
  README.md - by D3rrumbe
-->

<h1 align="center">🔍 Salesforce Aura Pentest Toolkit</h1>

<p align="center">
  <b>Herramienta profesional para pentesting de aplicaciones Salesforce Aura</b>
</p>

<p align="center">
  <a href="https://www.python.org/downloads/">
    <img src="https://img.shields.io/badge/python-3.6+-blue.svg" alt="Python 3.6+">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License">
  </a>
  <a href="https://developer.salesforce.com/docs/atlas.en-us.aura_dev_guide.meta/aura_dev_guide/">
    <img src="https://img.shields.io/badge/salesforce-aura-lightblue.svg" alt="Salesforce Aura">
  </a>
  <img src="https://img.shields.io/badge/status-stable-brightgreen.svg" alt="Status">
</p>

<p align="center">
  <a href="#-instalación">Instalación</a> •
  <a href="#-uso-rápido">Uso Rápido</a> •
  <a href="#-documentación">Documentación</a> •
  <a href="#-ejemplos">Ejemplos</a> •
  <a href="#-solución-de-problemas">Solución de Problemas</a>
</p>

---

## ⚠️ Disclaimer

> **🚨 IMPORTANTE: Esta herramienta es solo para fines educativos y pruebas de seguridad autorizadas.**
> 
> El uso no autorizado de esta herramienta contra sistemas que no te pertenecen es **ilegal** y puede constituir un delito informático. El autor no se hace responsable del uso indebido de esta herramienta.
>
> **Siempre obtén permiso por escrito antes de realizar pruebas de seguridad.**

---

## ✨ Características

| Característica | Descripción |
|:-------------|:------------|
| 🔎 **Diagnóstico Automático** | Detecta endpoints Aura válidos automáticamente |
| 🔐 **Bypass SSL** | Soporta entornos de prueba con certificados autofirmados |
| 📊 **Enumeración Completa** | Lista objetos, campos, registros y archivos |
| 💉 **Inyección SOQL/SOSL** | Pruebas automatizadas de inyección |
| 📄 **Reportes Detallados** | Exporta a TXT y JSON |
| 🌐 **Soporte Proxy** | Compatible con Burp Suite y otros proxies |
| 📝 **Logging Completo** | Registra todas las operaciones para análisis |

---

## 📋 Requisitos

- **Python**: 3.6 o superior
- **Sistema Operativo**: Linux, macOS, Windows
- **Dependencias**: `requests`, `urllib3`

### Instalar Dependencias

```
pip install requests urllib3
🚀 Instalación Rápida
Opción 1: Clonar Repositorio
bash
# Clonar
git clone https://github.com/tuusuario/salesforce-aura-pentest.git
cd salesforce-aura-pentest

# Hacer ejecutables
chmod +x diagnose_aura.py aura_pentest.py

# Verificar instalación
python3 diagnose_aura.py --help
Opción 2: Descargar Directamente

# Descargar scripts
curl -O https://raw.githubusercontent.com/tuusuario/salesforce-aura-pentest/main/diagnose_aura.py
curl -O https://raw.githubusercontent.com/tuusuario/salesforce-aura-pentest/main/aura_pentest.py

# Hacer ejecutables
chmod +x diagnose_aura.py aura_pentest.py
📖 Uso Rápido
Paso 1: Obtener Cookies del Navegador
Abre tu navegador y navega a tu organización Salesforce
Inicia sesión con tus credenciales
Abre DevTools (F12) → Application → Cookies
Copia los valores de:
sid (Session ID)
BrowserId
Paso 2: Diagnóstico de Conexión

python3 diagnose_aura.py \
  -u https://org--sandbox.my.salesforce.com \
  -c "sid=TU_SID_AQUI;BrowserId=TU_BROWSER_ID" \
  -v
Paso 3: Ejecutar Pentest Completo
bash
python3 aura_pentest.py \
  -u https://org--sandbox.my.salesforce.com \
  -c "sid=TU_SID_AQUI;BrowserId=TU_BROWSER_ID" \
  -t "TU_AURA_TOKEN" \
  -f "TU_FWUID" \
  --full \
  -v \
  -o reporte.txt \
  --export-json resultados.json
📋 Parámetros Disponibles
Parámetros Comunes (Ambos Scripts)
Parámetro	Corto	Requerido	Descripción	Ejemplo
--url	-u	✅	URL base del sitio Salesforce	https://org--sandbox.my.salesforce.com
--cookie	-c	✅	Cookies de sesión	sid=ABC...;BrowserId=XYZ...
--proxy	-p	❌	Proxy HTTP/HTTPS	http://127.0.0.1:8080
--timeout		❌	Timeout en segundos (default: 15)	30
--verbose	-v	❌	Modo verbose con más detalle	-
Parámetros Específicos de aura_pentest.py
Parámetro	Descripción
--aura-token	Aura JWT token para autenticación
--fwuid	Framework UID del contexto Aura
--full	Ejecutar todas las fases de pentest
--recon-only	Solo fase de reconocimiento
--enum-only	Solo enumeración de datos
--sqli-test	Solo pruebas de inyección
--object	Enumerar objeto específico
--search-term	Término de búsqueda para registros
--max-pages	Máximo de páginas para extracción
--output	Archivo de reporte (formato TXT)
--export-json	Exportar resultados (formato JSON)
--aura-endpoint	Endpoint específico (ej: /aura)
💡 Ejemplos de Uso
Ejemplo 1: Diagnóstico Básico

python3 diagnose_aura.py \
  -u https://miorg--sandbox.my.salesforce.com \
  -c "sid=00DABC123...;BrowserId=XYZ789..." \
  -v
Salida esperada:

================================================================================
DIAGNÓSTICO DE CONEXIÓN AURA
================================================================================
Target: https://miorg--sandbox.my.salesforce.com
Cookies: ['sid', 'BrowserId']

[*] Test 1: Verificando conexión básica...
    Status: 200
    ✅ Conexión exitosa - Sesión válida

[*] Test 2: Probando endpoints Aura...
    ✅ /aura: 200 - ENDPOINT AURA VÁLIDO

✅ Endpoints encontrados: 1
   - /aura
Ejemplo 2: Pentest Completo

python3 aura_pentest.py \
  -u https://miorg--sandbox.my.salesforce.com \
  -c "sid=00DABC123...;BrowserId=XYZ789..." \
  -t "eyJhbGciOiJIUzI1NiIs..." \
  -f "UlhVUlZGb3VNNThU..." \
  --full \
  -v \
  -o "reporte_$(date +%Y%m%d_%H%M%S).txt" \
  --export-json "resultados_$(date +%Y%m%d_%H%M%S).json" \
  2>&1 | tee "ejecucion.log"
Ejemplo 3: Solo Enumerar Objeto Account

python3 aura_pentest.py \
  -u https://miorg--sandbox.my.salesforce.com \
  -c "sid=...;BrowserId=..." \
  --enum-only \
  --object "Account" \
  --max-pages 5 \
  -v
Ejemplo 4: Con Proxy (Burp Suite)

python3 aura_pentest.py \
  -u https://miorg--sandbox.my.salesforce.com \
  -c "sid=...;BrowserId=..." \
  -t "eyJ..." \
  -f "UlhVU..." \
  --proxy http://127.0.0.1:8080 \
  --full \
  -v
Ejemplo 5: Solo Pruebas de Inyección SOQL

python3 aura_pentest.py \
  -u https://miorg--sandbox.my.salesforce.com \
  -c "sid=...;BrowserId=..." \
  -t "eyJ..." \
  --sqli-test \
  -v

📁 Estructura del Proyecto
salesforce-aura-pentest/
├── README.md              # Este archivo
├── LICENSE                # Licencia MIT
├── .gitignore            # Archivos ignorados por git
├── requirements.txt      # Dependencias Python
├── diagnose_aura.py      # Script de diagnóstico
├── aura_pentest.py       # Script principal de pentest
└── examples/             # Ejemplos adicionales
    ├── basic_diagnosis.sh
    └── full_pentest.sh
🔧 Solución de Problemas
❌ Error SSL: WRONG_VERSION_NUMBER
Causa: Incompatibilidad de versiones SSL/TLS o proxy corporativo.

Solución:


# Deshabilitar proxy del sistema
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy

# Ejecutar nuevamente
python3 aura_pentest.py -u <URL> -c <COOKIES> ...
El script ya incluye session.verify = False para entornos de prueba.

❌ Error de Proxy: Your proxy appears to only use HTTP
Causa: Variables de entorno de proxy configuradas.

Solución:


# Deshabilitar variables de proxy
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy

# O ejecutar en subshell limpio
(env -u HTTP_PROXY -u HTTPS_PROXY python3 aura_pentest.py ...)
❌ Sesión Expirada (302 Redirect a login)
Síntoma: Status 302 con Location hacia /login

Solución:

Abre el navegador y navega al sitio Salesforce
Inicia sesión nuevamente con tus credenciales
Abre DevTools (F12) → Application → Cookies
Copia los valores frescos de sid y BrowserId
Actualiza el comando con las nuevas cookies
💡 Tip: Las cookies de Salesforce generalmente expiran en 2-8 horas.

⏱️ Timeout en Requests
Solución: Aumenta el timeout:


python3 aura_pentest.py -u <URL> -c <COOKIES> --timeout 30 ...
🔍 No se Encuentra el Endpoint Aura
Solución: Especifica el endpoint manualmente:


python3 aura_pentest.py \
  -u <URL> \
  -c <COOKIES> \
  --aura-endpoint "/aura" \
  ...
Endpoints comunes a probar:

/aura (más común)
/s/aura
/s/sfsites/aura
/_ui/common/aura/AuraServlet

📄 Archivos de Salida
Archivo	Descripción
aura_pentest_YYYYMMDD_HHMMSS.log	Log completo de ejecución
reporte.txt	Reporte legible para humanos
resultados.json	Datos estructurados en JSON
ejecucion.log	Copia de salida de terminal
comando_pentest.sh	Script para reejecutar
🛡️ Seguridad y Privacidad
⚠️ Advertencias importantes:

Nunca compartas cookies de sesión (sid) en repositorios públicos
Usa .gitignore para excluir logs y archivos de configuración
Las cookies tienen tiempo de expiración limitado
No uses esta herramienta en producción sin autorización
Deshabilita SSL solo en entornos de prueba controlados
.gitignore Recomendado
gitignore
# Logs
*.log
aura_pentest_*.log

# Output files
reporte*.txt
resultados*.json

# Sensitive data
cookies.txt
tokens.txt
config.ini
🤝 Contribuciones
Las contribuciones son bienvenidas. Por favor:

Fork el repositorio
Crea una rama (git checkout -b feature/nueva-funcionalidad)
Commit tus cambios (git commit -am 'Agrega nueva funcionalidad')
Push a la rama (git push origin feature/nueva-funcionalidad)
Abre un Pull Request
Reportar Bugs
Usa GitHub Issues para reportar bugs o solicitar funcionalidades.

📝 Roadmap
 Soporte para autenticación OAuth
 Interfaz gráfica (GUI)
 Exportación a XML y CSV
 Integración con Burp Suite Extension
 Soporte para SOQL injection time-based
 Módulo de fuerza bruta de objetos
 Soporte multi-threading
📚 Recursos Adicionales
Salesforce Aura Developer Guide
Salesforce Security Guide
OWASP Testing Guide
📄 Licencia
Este proyecto está licenciado bajo la Licencia MIT - ver el archivo LICENSE para detalles.

MIT License

Copyright (c) 2024 [D3rrumbe]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
<p align="center"> <b>Desarrollado con ❤️ para la comunidad de seguridad</b> </p><p align="center"> <i>"Conocimiento es poder, pero el poder conlleva responsabilidad"</i> </p> ```
