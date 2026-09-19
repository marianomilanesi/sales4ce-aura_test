#!/usr/bin/env python3
"""
diagnose_aura.py - Script de diagnóstico para problemas de endpoint Aura
Uso: python3 diagnose_aura.py -u <url> -c <cookie> -t <token> -f <fwuid>
"""

import requests
import urllib.parse
import json
import sys
import argparse
import os


def parse_arguments():
    """Parsea argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description='Diagnóstico de conexión Salesforce Aura',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Ejemplos:
  # Diagnóstico básico
  python3 diagnose_aura.py -u https://miorg--sandbox.my.salesforce.com -c "sid=..."
  
  # Con todos los parámetros
  python3 diagnose_aura.py \\
    -u https://miorg--sandbox.my.salesforce.com \\
    -c "sid=ABC...;BrowserId=XYZ..." \\
    -t "eyJ..." \\
    -f "UlhVU..."
        '''
    )
    
    parser.add_argument('-u', '--url', required=True,
                       help='URL base del sitio Salesforce (ej: https://miorg--sandbox.my.salesforce.com)')
    
    parser.add_argument('-c', '--cookie', required=True,
                       help='Cookies de sesión (ej: sid=ABC...;BrowserId=XYZ...)')
    
    parser.add_argument('-t', '--token',
                       help='Aura token JWT (opcional)')
    
    parser.add_argument('-f', '--fwuid',
                       help='Framework UID (opcional)')
    
    parser.add_argument('-p', '--proxy',
                       help='Proxy (opcional, ej: http://127.0.0.1:8080)')
    
    parser.add_argument('--timeout', type=int, default=15,
                       help='Timeout en segundos (default: 15)')
    
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Modo verbose')
    
    return parser.parse_args()


def parse_cookies(cookie_string: str) -> dict:
    """Parsea string de cookies a diccionario"""
    cookies = {}
    
    # Limpiar prefijo "Cookie:" si existe
    if "Cookie:" in cookie_string:
        cookie_string = cookie_string.split("Cookie:", 1)[1].strip()
    
    for cookie in cookie_string.split(';'):
        if '=' in cookie:
            name, value = cookie.strip().split('=', 1)
            cookies[name] = value
    
    return cookies


def diagnose_connection(base_url: str, cookies: dict, proxy: str = None, timeout: int = 15, verbose: bool = False):
    """Diagnostica la conexión con Salesforce Aura"""
    
    print("=" * 80)
    print("DIAGNÓSTICO DE CONEXIÓN AURA")
    print("=" * 80)
    print(f"Target: {base_url}")
    print(f"Cookies: {list(cookies.keys())}")
    if proxy:
        print(f"Proxy: {proxy}")
    print()
    
    # Crear sesión
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:156.0) Gecko/20100101 Firefox/156.0",
        "Accept": "*/*",
        "Accept-Language": "es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7",
    })
    
    # FIX SSL: Deshabilitar verificación SSL
    session.verify = False
    
    # Configurar proxy si se especificó
    if proxy:
        session.proxies = {"http": proxy, "https": proxy}
    
    # Configurar cookies
    for name, value in cookies.items():
        session.cookies.set(name, value)
    
    # Test 1: Verificar conexión básica
    print("[*] Test 1: Verificando conexión básica...")
    try:
        response = session.get(
            f"{base_url}/lightning/page/home",
            timeout=timeout,
            allow_redirects=False
        )
        print(f"    Status: {response.status_code}")
        
        if response.status_code == 200:
            print("    ✅ Conexión exitosa - Sesión válida")
        elif response.status_code == 302:
            location = response.headers.get('Location', '')
            print(f"    ⚠️  Redirección detectada")
            print(f"    Location: {location}")
            if "login" in location.lower():
                print("    ❌ SESIÓN EXPIRADA - Necesitas obtener cookies frescas")
                return False
        elif response.status_code == 401:
            print("    ❌ No autorizado - Sesión inválida")
            return False
        else:
            print(f"    ⚠️  Status inesperado: {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("    ❌ Timeout - Problema de red")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"    ❌ Error de conexión: {e}")
        return False
    except Exception as e:
        print(f"    ❌ Error: {e}")
        return False
    
    print()
    
    # Test 2: Probar endpoints Aura
    print("[*] Test 2: Probando endpoints Aura...")
    
    endpoints = [
        "/aura",
        "/s/aura",
        "/s/sfsites/aura",
        "/_ui/common/aura/AuraServlet",
        "/lightning/aura",
        "/sfsites/aura",
    ]
    
    working_endpoints = []
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        try:
            # Intentar POST con payload mínimo
            test_payload = {
                "message": json.dumps({"actions": []}),
                "aura.context": json.dumps({"mode": "PROD", "fwuid": "null"}),
                "aura.token": "null"
            }
            
            response = session.post(
                url,
                data=test_payload,
                timeout=timeout,
                allow_redirects=False
            )
            
            status = response.status_code
            content_type = response.headers.get('Content-Type', 'unknown')
            
            if status == 200:
                try:
                    data = response.json()
                    if "actions" in data or "context" in data or "exceptionEvent" in data:
                        print(f"    ✅ {endpoint}: {status} - ENDPOINT AURA VÁLIDO")
                        working_endpoints.append(url)
                    else:
                        print(f"    📝 {endpoint}: {status} - Respuesta JSON pero no Aura")
                except:
                    print(f"    📝 {endpoint}: {status} - No es JSON")
            elif status == 302:
                print(f"    ⚠️  {endpoint}: {status} - Redirección")
            elif status == 404:
                print(f"    ❌ {endpoint}: {status} - No encontrado")
            else:
                print(f"    📝 {endpoint}: {status} - {content_type[:30]}")
                
        except Exception as e:
            if verbose:
                print(f"    💥 {endpoint}: Error - {str(e)[:50]}")
    
    print()
    
    # Resultado
    print("=" * 80)
    print("RESULTADO DEL DIAGNÓSTICO")
    print("=" * 80)
    
    if working_endpoints:
        print(f"\n✅ ENDPOINTS AURA ENCONTRADOS: {len(working_endpoints)}")
        for ep in working_endpoints:
            print(f"   - {ep}")
        print(f"\n💡 Usa este endpoint en tu script:")
        print(f'   --aura-endpoint "{working_endpoints[0].replace(base_url, "")}"')
        return working_endpoints[0].replace(base_url, "")
    else:
        print("\n❌ NO SE ENCONTRARON ENDPOINTS AURA")
        print("\nPosibles causas:")
        print("   1. La sesión (SID) expiró")
        print("   2. El sitio no usa Aura (puede ser LWC puro)")
        print("   3. Hay un WAF bloqueando requests")
        print("   4. El endpoint está en una ruta no estándar")
        print("\n💡 Solución: Obtén cookies frescas del navegador")
        return None


def test_specific_endpoint(base_url: str, cookies: dict, token: str, fwuid: str, 
                          proxy: str = None, timeout: int = 15):
    """Prueba un endpoint específico con ListUi.getListObjectInfo"""
    
    print("\n" + "=" * 80)
    print("TEST ESPECÍFICO - ListUi.getListObjectInfo")
    print("=" * 80)
    
    session = requests.Session()
    session.verify = False  # FIX SSL
    
    if proxy:
        session.proxies = {"http": proxy, "https": proxy}
    
    for name, value in cookies.items():
        session.cookies.set(name, value)
    
    # Payload de prueba
    payload = {
        'message': json.dumps({
            "actions": [{
                "id": "1152;a",
                "descriptor": "aura://ListUiController/ACTION$getListObjectInfo",
                "callingDescriptor": "UNKNOWN",
                "params": {
                    "objectApiName": "Account"
                }
            }]
        }),
        'aura.context': json.dumps({
            "mode": "PROD",
            "fwuid": fwuid if fwuid else "null",
            "app": "one:one",
            "loaded": {"APPLICATION@markup://one:one": ""},
            "dn": [],
            "globals": {},
            "uad": True
        }),
        'aura.pageURI': '/lightning/r/Account/home',
        'aura.token': token if token else "null"
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        "Origin": base_url,
        "Referer": f"{base_url}/lightning/r/Account/home",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    # Probar diferentes endpoints
    endpoints = ["/aura", "/s/sfsites/aura", "/s/aura"]
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}?r=52&aura.ListUi.getListObjectInfo=1"
        print(f"\n[*] Probando: {url}")
        
        try:
            response = session.post(
                url,
                data=payload,
                headers=headers,
                timeout=timeout
            )
            
            print(f"    Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"    ✅ Respuesta JSON recibida")
                    
                    if "actions" in data:
                        actions = data.get("actions", [])
                        print(f"    Actions: {len(actions)}")
                        
                        for action in actions:
                            return_value = action.get("returnValue", {})
                            if return_value:
                                print(f"    ✅ Request exitoso!")
                                print(f"\n    💡 El endpoint válido es: {endpoint}")
                                return endpoint
                            else:
                                error = action.get("error", [])
                                if error:
                                    print(f"    ⚠️  Error en action: {error}")
                    
                    elif "exceptionEvent" in data:
                        print(f"    ⚠️  Exception: {data.get('exceptionEvent', {})}")
                        
                except json.JSONDecodeError:
                    print(f"    ❌ No es JSON válido")
                    print(f"    Preview: {response.text[:200]}")
            else:
                print(f"    ❌ Error HTTP {response.status_code}")
                    
        except Exception as e:
            print(f"    💥 Error: {e}")
    
    return None


def generate_command(base_url: str, cookies: str, token: str, fwuid: str, endpoint: str):
    """Genera el comando para ejecutar el pentest"""
    
    print("\n" + "=" * 80)
    print("COMANDO PARA EJECUTAR PENTEST")
    print("=" * 80)
    
    cmd = f"""python3 aura_test.py \\
  -u {base_url} \\
  --cookie "{cookies}" \\
  --aura-token "{token}" \\
  --fwuid "{fwuid}" \\
  --aura-endpoint "{endpoint}" \\
  --full -v"""
    
    print(cmd)
    print()
    
    # Guardar a archivo
    with open("comando_pentest.sh", "w") as f:
        f.write("#!/bin/bash\n")
        f.write(cmd + "\n")
    
    print("💡 Comando guardado en: comando_pentest.sh")
    print("   Ejecuta: chmod +x comando_pentest.sh && ./comando_pentest.sh")


if __name__ == "__main__":
    print("\n🔍 DIAGNÓSTICO DE SALESFORCE AURA\n")
    
    # Parsear argumentos
    args = parse_arguments()
    
    # Parsear cookies
    cookies = parse_cookies(args.cookie)
    
    # Ejecutar diagnóstico
    endpoint = diagnose_connection(
        args.url, 
        cookies, 
        args.proxy, 
        args.timeout, 
        args.verbose
    )
    
    # Si no se encontró endpoint, intentar test específico
    if not endpoint and args.token and args.fwuid:
        endpoint = test_specific_endpoint(
            args.url,
            cookies,
            args.token,
            args.fwuid,
            args.proxy,
            args.timeout
        )
    
    # Generar comando final
    if endpoint and args.token and args.fwuid:
        generate_command(args.url, args.cookie, args.token, args.fwuid, endpoint)
    else:
        print("\n❌ No se pudo determinar el endpoint automáticamente")
        print("   Proporciona --token y --fwuid para un test más completo")
