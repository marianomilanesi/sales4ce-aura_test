#!/usr/bin/env python3
"""
Salesforce Aura Advanced Penetration Testing Tool v2.0
=====================================================
Corregido con:
- Logging completo a archivo y consola
- Fix SSL (bypass verificación)
- Manejo de errores mejorado

Autor: D3rrumbe
Versión: 2.0.1
"""

import argparse
import json
import re
import sys
import urllib.parse
import base64
import time
import random
import string
import ssl
import urllib3
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field, asdict
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ============================================
# CONFIGURACIÓN DE LOGGING (CORREGIDO)
# ============================================
import logging

# Crear logger principal
logger = logging.getLogger('aura_pentest')
logger.setLevel(logging.DEBUG)

# Handler para archivo
LOG_FILENAME = f"aura_pentest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
file_handler = logging.FileHandler(LOG_FILENAME, mode='w')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler.setFormatter(file_formatter)

# Handler para consola
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(message)s')
console_handler.setFormatter(console_formatter)

# Agregar handlers
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# FIX SSL: Deshabilitar warnings de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Log inicial
logger.info("="*80)
logger.info("SALESFORCE AURA PENTEST - INICIO")
logger.info(f"Log file: {LOG_FILENAME}")
logger.info("="*80)

# Redirigir excepciones al log
def log_exception(exc_type, exc_value, exc_traceback):
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = log_exception


# ============================================================================
# CONSTANTES
# ============================================================================

AURA_ENDPOINTS = [
    "/aura",  # ← Endpoint correcto para tu caso
    "/s/sfsites/aura",
    "/s/aura",
    "/_ui/common/aura/AuraServlet",
]

DEFAULT_HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9,es-ES;q=0.8,es;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": None,
    "Referer": None,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:156.0) Gecko/20100101 Firefox/156.0"
}

DEFAULT_AURA_CONTEXT = {
    "mode": "PROD",
    "fwuid": "null",
    "app": "one:one",
    "loaded": {"APPLICATION@markup://one:one": ""},
    "dn": [],
    "globals": {},
    "uad": False
}

CONTROLLERS = {
    "host_config": "serviceComponent://ui.force.components.controllers.hostConfig.HostConfigController/ACTION$getConfigData",
    "router_initializer": "aura://ComponentController/ACTION$getComponent",
    "record_ui": "aura://RecordUiController/ACTION$getObjectInfo",
    "record_gvp": "serviceComponent://ui.force.components.controllers.recordGlobalValueProvider.RecordGvpController/ACTION$getRecord",
    "list_ui": "aura://ListUiController/ACTION$getListObjectInfo",
    "selectable_list": "serviceComponent://ui.force.components.controllers.lists.selectableListDataProvider.SelectableListDataProviderController/ACTION$getItems",
    "scoped_search": "serviceComponent://ui.search.components.forcesearch.scopedresultsdataprovider.ScopedResultsDataProviderController/ACTION$getLookupItems",
    "graphql": "aura://RecordUiController/ACTION$executeGraphQL",
    "self_register": "apex://LightningSelfRegisterController/ACTION$registerUser",
    "login": "apex://LightningLoginFormController/ACTION$login",
    "forgot_password": "apex://LightningForgotPasswordController/ACTION$forgotPassword"
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class AuraEndpoint:
    descriptor: str
    params: List[Dict[str, Any]]
    component_type: str
    source: str
    return_type: Optional[str] = None
    is_vulnerable: bool = False
    vulnerabilities: List[str] = field(default_factory=list)

@dataclass
class Route:
    page_id: str
    view_uuid: str
    theme_layout_type: str
    route_path: str = ""
    is_protected: bool = False
    
@dataclass
class SObject:
    api_name: str
    label: str = ""
    fields: List[Dict] = field(default_factory=list)
    child_relationships: List[Dict] = field(default_factory=list)
    record_count: int = 0
    is_custom: bool = False
    is_queryable: bool = True

@dataclass
class SQLiTestResult:
    endpoint: str
    test_type: str
    payload: str
    is_vulnerable: bool
    evidence: str
    response_time: float
    error_indicators: List[str] = field(default_factory=list)

@dataclass
class Vulnerability:
    type: str
    severity: str
    endpoint: str
    description: str
    evidence: str
    remediation: str
    payload: Optional[str] = None


# ============================================================================
# CLASE PRINCIPAL
# ============================================================================

class SalesforceAuraAnalyzer:
    
    def __init__(self, base_url: str, cookies: str = None, 
                 proxy: str = None, timeout: int = 30,
                 aura_token: str = None, aura_context: str = None,
                 fwuid: str = None, verbose: bool = False):
        
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.timeout = timeout
        self.verbose = verbose
        self.aura_endpoint = None
        
        # FIX SSL: Deshabilitar verificación SSL
        self.session.verify = False
        
        # Configurar headers
        self.session.headers.update(DEFAULT_HEADERS)
        self.session.headers["Origin"] = self.base_url
        self.session.headers["Referer"] = f"{self.base_url}/"
        
        # Contexto Aura
        self.aura_context = self._parse_aura_context(aura_context, fwuid)
        self.aura_token = aura_token if aura_token else "null"
        self.render_ctx = None
        
        # Configurar retries
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST", "GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Configurar cookies
        if cookies:
            self._parse_cookies(cookies)
        
        # Configurar proxy
        if proxy:
            self.session.proxies = {"http": proxy, "https": proxy}
            logger.info(f"[+] Proxy configurado: {proxy}")
        
        # Almacenamiento de resultados
        self.routes: List[Route] = []
        self.endpoints: List[AuraEndpoint] = []
        self.objects: List[SObject] = []
        self.files_found: List[Dict] = []
        self.vulnerabilities: List[Vulnerability] = []
        self.sqli_results: List[SQLiTestResult] = []
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.5
        
        logger.info(f"[+] Analizador inicializado para: {self.base_url}")
        logger.info(f"[+] Aura Token: {'Configurado' if self.aura_token != 'null' else 'No configurado'}")
        logger.info(f"[+] FWUID: {self.aura_context.get('fwuid', 'null')[:30]}...")
        
    def _parse_aura_context(self, aura_context: Optional[str], fwuid: Optional[str]) -> Dict:
        context = DEFAULT_AURA_CONTEXT.copy()
        
        if aura_context:
            try:
                parsed = json.loads(aura_context)
                context.update(parsed)
                logger.info("[+] Contexto Aura personalizado cargado")
            except json.JSONDecodeError as e:
                logger.error(f"[!] Error parseando aura.context: {e}")
        
        if fwuid:
            context["fwuid"] = fwuid
            logger.info(f"[+] FWUID sobrescrito: {fwuid[:30]}...")
            
        return context
    
    def _parse_cookies(self, cookie_string: str):
        if "Cookie:" in cookie_string:
            cookie_string = cookie_string.split("Cookie:", 1)[1].strip()
        
        if ":" in cookie_string and "=" in cookie_string.split(":", 1)[0]:
            lines = cookie_string.split("\n")
            for line in lines:
                if line.startswith("Cookie:"):
                    cookie_string = line.split(":", 1)[1].strip()
                    break
        
        for cookie in cookie_string.split(';'):
            if '=' in cookie:
                name, value = cookie.strip().split('=', 1)
                self.session.cookies.set(name, value)
                if self.verbose:
                    logger.debug(f"    [Cookie] {name}={value[:20]}...")
    
    def _rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _build_aura_payload(self, actions: List[Dict], 
                           context: Dict = None,
                           page_uri: str = "/") -> Dict[str, str]:
        ctx = context or self.aura_context
        
        payload = {
            "message": json.dumps({"actions": actions}),
            "aura.context": json.dumps(ctx),
            "aura.pageURI": page_uri,
            "aura.token": self.aura_token
        }
        
        return payload
    
    def _send_aura_request(self, actions: List[Dict], 
                          context: Dict = None,
                          page_uri: str = "/",
                          extra_headers: Dict = None) -> Optional[Dict]:
        self._rate_limit()
        
        if not self.aura_endpoint:
            if not self._discover_aura_endpoint():
                logger.error("[-] No se pudo descubrir el endpoint Aura")
                return None
        
        payload = self._build_aura_payload(actions, context, page_uri)
        
        headers = self.session.headers.copy()
        if extra_headers:
            headers.update(extra_headers)
        
        try:
            logger.debug(f"[Request] POST {self.aura_endpoint}")
            response = self.session.post(
                self.aura_endpoint,
                data=payload,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=False
            )
            
            logger.debug(f"[Response] {response.status_code}")
            
            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return self._parse_js_response(response.text)
            elif response.status_code == 302:
                logger.warning("[!] Redirección detectada (posible sesión expirada)")
                return None
            else:
                logger.debug(f"[-] Error HTTP {response.status_code}")
                return None
                
        except requests.exceptions.ProxyError as e:
            logger.error(f"[-] Error de proxy: {e}")
            return None
        except requests.exceptions.Timeout:
            logger.error("[-] Timeout en request")
            return None
        except Exception as e:
            logger.error(f"[-] Error en request: {e}")
            return None
    
    def _parse_js_response(self, text: str) -> Optional[Dict]:
        try:
            match = re.search(r'\((\{.*\})\)', text, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            return json.loads(text)
        except:
            return {"raw_response": text[:500]}
    
    def _discover_aura_endpoint(self) -> bool:
        logger.info("[*] Descubriendo endpoint Aura...")
        
        test_action = [{
            "id": "1;a",
            "descriptor": CONTROLLERS["host_config"],
            "callingDescriptor": "UNKNOWN",
            "params": {}
        }]
        
        for endpoint in AURA_ENDPOINTS:
            url = f"{self.base_url}{endpoint}"
            try:
                payload = self._build_aura_payload(test_action)
                logger.debug(f"Probando: {url}")
                response = self.session.post(url, data=payload, timeout=15)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if "actions" in data or "context" in data:
                            self.aura_endpoint = url
                            logger.info(f"[+] Endpoint Aura encontrado: {endpoint}")
                            
                            if self.aura_context.get("fwuid") == "null":
                                self._extract_fwuid(data)
                            return True
                    except:
                        pass
                        
            except Exception as e:
                logger.debug(f"Error con {endpoint}: {e}")
                continue
        
        logger.error("[-] No se encontró ningún endpoint Aura válido")
        return False
    
    def _extract_fwuid(self, response: Dict):
        try:
            if "context" in response and "fwuid" in response["context"]:
                self.aura_context["fwuid"] = response["context"]["fwuid"]
                logger.info(f"[+] FWUID extraído: {self.aura_context['fwuid'][:30]}...")
        except:
            pass

    # [Aquí van el resto de los métodos: enumerate_routes, analyze_global_layout, 
    # hydrate_pages, enumerate_objects, enumerate_fields, dump_records, 
    # test_soql_injection_comprehensive, generate_report, etc.]
    # Por brevedad, incluyo solo los métodos esenciales:

    def enumerate_routes(self) -> List[Route]:
        logger.info("\n[*] Fase 1.1: Enumerando rutas...")
        
        routes = []
        action = [{
            "descriptor": CONTROLLERS["router_initializer"],
            "params": {
                "name": "markup://siteforce:routerInitializer",
                "params": {}
            }
        }]
        
        response = self._send_aura_request(action)
        if response:
            routes = self._parse_routes(response)
        
        self.routes.extend(routes)
        logger.info(f"[+] {len(routes)} rutas descubiertas")
        
        return routes
    
    def _parse_routes(self, response: Dict) -> List[Route]:
        routes = []
        try:
            actions = response.get("actions", [])
            for action in actions:
                return_value = action.get("returnValue", {})
                components = return_value.get("components", [])
                
                for comp in components:
                    route_info = self._extract_route_info(comp)
                    if route_info:
                        routes.append(route_info)
        except Exception as e:
            logger.error(f"[-] Error parseando rutas: {e}")
        
        return routes
    
    def _extract_route_info(self, component: Dict) -> Optional[Route]:
        try:
            if isinstance(component, dict):
                page_id = (component.get("id") or 
                          component.get("pageId") or 
                          component.get("page_id", ""))
                
                view_uuid = (component.get("view_uuid") or 
                            component.get("viewId") or 
                            component.get("view_id", ""))
                
                theme_layout = component.get("themeLayoutType", "Inner")
                route_path = component.get("routePath", component.get("path", ""))
                
                if page_id:
                    return Route(
                        page_id=page_id,
                        view_uuid=view_uuid,
                        theme_layout_type=theme_layout,
                        route_path=route_path
                    )
        except:
            pass
        return None

    def enumerate_objects(self) -> List[str]:
        logger.info("\n[*] Fase 4.1: Enumerando objetos...")
        
        action = [{
            "id": "1;a",
            "descriptor": CONTROLLERS["host_config"],
            "callingDescriptor": "UNKNOWN",
            "params": {}
        }]
        
        response = self._send_aura_request(action)
        
        objects = []
        if response:
            objects = self._parse_objects_from_config(response)
            logger.info(f"[+] {len(objects)} objetos encontrados")
            
            for obj_name in objects:
                is_custom = obj_name.endswith("__c")
                self.objects.append(SObject(
                    api_name=obj_name,
                    is_custom=is_custom
                ))
        
        return objects
    
    def _parse_objects_from_config(self, response: Dict) -> List[str]:
        objects = []
        try:
            actions = response.get("actions", [])
            for action in actions:
                return_value = action.get("returnValue", {})
                
                if "objects" in return_value:
                    for obj in return_value["objects"]:
                        if isinstance(obj, str):
                            objects.append(obj)
                        elif isinstance(obj, dict):
                            if "apiName" in obj:
                                objects.append(obj["apiName"])
                            elif "name" in obj:
                                objects.append(obj["name"])
        except:
            pass
        
        return objects

    def generate_report(self, output_file: str = None) -> str:
        report = []
        report.append("=" * 80)
        report.append("SALESFORCE AURA PENTEST REPORT - v2.0")
        report.append("=" * 80)
        report.append(f"Target: {self.base_url}")
        report.append(f"Aura Endpoint: {self.aura_endpoint}")
        report.append(f"Fecha: {datetime.now().isoformat()}")
        report.append("")
        
        report.append("-" * 40)
        report.append("AURA CONTEXT")
        report.append("-" * 40)
        report.append(json.dumps(self.aura_context, indent=2))
        report.append("")
        
        report.append("-" * 40)
        report.append(f"OBJECTS DISCOVERED ({len(self.objects)})")
        report.append("-" * 40)
        for obj in self.objects:
            report.append(f"  - {obj.api_name}")
            report.append(f"    Custom: {obj.is_custom}")
            report.append(f"    Fields: {len(obj.fields)}")
            report.append(f"    Record Count: {obj.record_count}")
            report.append("")
        
        report_str = "\n".join(report)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_str)
            logger.info(f"\n[+] Reporte guardado en: {output_file}")
        
        return report_str
    
    def export_to_json(self, output_file: str):
        data = {
            "target": self.base_url,
            "aura_endpoint": self.aura_endpoint,
            "aura_context": self.aura_context,
            "routes": [asdict(r) for r in self.routes],
            "endpoints": [asdict(e) for e in self.endpoints],
            "objects": [asdict(o) for o in self.objects],
            "files": self.files_found,
            "vulnerabilities": [asdict(v) for v in self.vulnerabilities],
            "sqli_results": [asdict(s) for s in self.sqli_results]
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"[+] Datos exportados a: {output_file}")


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Salesforce Aura Advanced Penetration Testing Tool v2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("-u", "--url", required=True,
                       help="URL base del sitio Salesforce")
    parser.add_argument("-c", "--cookie",
                       help="Cookies de sesión")
    parser.add_argument("-p", "--proxy",
                       help="Proxy (formato: http://host:port)")
    parser.add_argument("-o", "--output",
                       help="Archivo de salida para el reporte")
    parser.add_argument("--export-json",
                       help="Exportar resultados a JSON")
    parser.add_argument("--timeout", type=int, default=30,
                       help="Timeout para requests (default: 30)")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Modo verbose")
    parser.add_argument("--aura-token",
                       help="Aura JWT token")
    parser.add_argument("--fwuid",
                       help="Framework UID específico")
    parser.add_argument("--full", action="store_true",
                       help="Ejecutar todas las fases (default)")
    
    args = parser.parse_args()
    
    logger.info(f"[*] Inicializando Salesforce Aura Analyzer v2.0")
    logger.info(f"[*] Target: {args.url}")
    
    analyzer = SalesforceAuraAnalyzer(
        base_url=args.url,
        cookies=args.cookie,
        proxy=args.proxy,
        timeout=args.timeout,
        aura_token=args.aura_token,
        fwuid=args.fwuid,
        verbose=args.verbose
    )
    
    try:
        if not analyzer._discover_aura_endpoint():
            logger.error("[-] No se pudo descubrir el endpoint Aura. Abortando.")
            sys.exit(1)
        
        analyzer.enumerate_routes()
        analyzer.enumerate_objects()
        
        report = analyzer.generate_report(args.output)
        print("\n" + report)
        
        if args.export_json:
            analyzer.export_to_json(args.export_json)
        
    except KeyboardInterrupt:
        logger.info("\n[!] Interrumpido por usuario")
        analyzer.generate_report(args.output)
    except Exception as e:
        logger.error(f"\n[-] Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
