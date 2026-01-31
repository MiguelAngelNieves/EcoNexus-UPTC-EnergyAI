import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime


def cargar_anomalias():
    print("Cargando anomalias detectadas...")

    ruta_anomalias = Path("outputs/anomalias.csv")

    if not ruta_anomalias.exists():
        raise FileNotFoundError(
            f"No se encontró {ruta_anomalias}. "
            "Ejecuta 06_detector_anomalias.py primero."
        )

    df_anomalias = pd.read_csv(ruta_anomalias)
    df_anomalias["timestamp"] = pd.to_datetime(df_anomalias["timestamp"])

    print(f"anomalias cargadas: {len(df_anomalias):,}")
    print(f"Periodo: {df_anomalias['timestamp'].min()} a {df_anomalias['timestamp'].max()}")

    return df_anomalias


def agrupar_por_patron(df_anomalias: pd.DataFrame) -> pd.DataFrame:
    print("Agrupando anomalias por patrón...")

    patrones = (
        df_anomalias
        .groupby(["sede", "sector", "tipo_anomalia"])
        .agg({
            "diferencia_kwh": ["count", "sum", "mean", "max"],
            "severidad": lambda serie: (serie == "critica").sum(),
        })
        .round(2)
    )

    patrones.columns = [
        "cantidad_eventos",
        "desperdicio_total_kwh",
        "desperdicio_promedio_kwh",
        "desperdicio_maximo_kwh",
        "eventos_criticos",
    ]

    patrones = patrones.reset_index()
    patrones = patrones.sort_values("desperdicio_total_kwh", ascending=False)

    print(f"Patrones identificados: {len(patrones)}")
    return patrones


def generar_recomendacion_texto(row):
    sede = row["sede"]
    sector = row["sector"]
    tipo = row["tipo_anomalia"]
    cantidad = int(row["cantidad_eventos"])

    # Importante: NO cambiar el contenido de recomendaciones_base
    recomendaciones_base = {
        "consumo_nocturno_alto": {
            "laboratorios": {
                "problema": f"Se detectaron {cantidad} eventos de consumo nocturno elevado (0-6 AM) en laboratorios de {sede}.",
                "causa": "Equipos que permanecen encendidos durante la noche sin necesidad operativa.",
                "accion": "1. Auditar equipos que operan 24/7 (freezers, incubadoras, servidores)\n2. Identificar cuáles pueden apagarse en horario nocturno\n3. Implementar temporizadores o sensores de ocupación\n4. Establecer protocolo de apagado nocturno para equipos no críticos",
                "responsable": "Coordinador de Laboratorios",
            },
            "comedor": {
                "problema": f"Se detectaron {cantidad} eventos de consumo nocturno en comedores de {sede}.",
                "causa": "Refrigeradores o sistemas de ventilación operando a máxima capacidad innecesariamente.",
                "accion": "1. Verificar configuración de termostatos de refrigeradores\n2. Revisar estado de empaques y sellos\n3. Reducir temperatura de refrigeración nocturna\n4. Apagar equipos no esenciales",
                "responsable": "Administrador de Servicios Alimentarios",
            },
            "salones": {
                "problema": f"Se detectaron {cantidad} eventos de consumo nocturno en salones de {sede}.",
                "causa": "Luces, aires acondicionados o proyectores dejados encendidos.",
                "accion": "1. Implementar sensores de movimiento para iluminación\n2. Temporizadores para aires acondicionados\n3. Capacitar al personal de aseo sobre apagado de equipos\n4. Rondas nocturnas de verificación",
                "responsable": "Servicios Generales",
            },
            "oficinas": {
                "problema": f"Se detectaron {cantidad} eventos de consumo nocturno en oficinas de {sede}.",
                "causa": "Computadores, luces o aires acondicionados sin apagar.",
                "accion": "1. Política de apagado obligatorio de equipos al salir\n2. Apagado automático de computadores después de 2 horas de inactividad\n3. Sensores de movimiento para iluminación\n4. Inspección semanal nocturna",
                "responsable": "Jefe de Área Administrativa",
            },
        },
        "consumo_fin_semana_alto": {
            "laboratorios": {
                "problema": f"Se detectaron {cantidad} eventos de consumo elevado en fines de semana en laboratorios de {sede}.",
                "causa": "Equipos operando sin actividades programadas o personal presente.",
                "accion": "1. Protocolo de cierre de laboratorios los fines de semana\n2. Lista de equipos autorizados para operar 24/7\n3. Sistema de solicitud para uso de laboratorios en fin de semana\n4. Inspección al cierre del viernes",
                "responsable": "Coordinador de Laboratorios",
            },
            "comedor": {
                "problema": f"Se detectaron {cantidad} eventos de consumo en comedores durante fines de semana en {sede}.",
                "causa": "Refrigeradores operando a capacidad normal sin demanda.",
                "accion": "1. Reducir temperatura de refrigeración los fines de semana\n2. Consolidar alimentos en menos refrigeradores\n3. Apagar equipos de cocción\n4. Verificar cierre correcto de instalaciones",
                "responsable": "Administrador de Servicios Alimentarios",
            },
            "salones": {
                "problema": f"Se detectaron {cantidad} eventos de consumo en salones durante fines de semana en {sede}.",
                "causa": "Instalaciones vacías con equipos encendidos.",
                "accion": "1. Apagado total de aires acondicionados los fines de semana\n2. Corte de energía en sectores no críticos\n3. Protocolo de verificación viernes en la tarde\n4. Activar solo salones con eventos programados",
                "responsable": "Servicios Generales",
            },
            "oficinas": {
                "problema": f"Se detectaron {cantidad} eventos de consumo en oficinas durante fines de semana en {sede}.",
                "causa": "Equipos de oficina sin apagar.",
                "accion": "1. Apagado de servidores no críticos\n2. Desconexión de equipos periféricos\n3. Sistema de alarma vinculado a consumo eléctrico\n4. Lista de equipos autorizados fin de semana",
                "responsable": "Jefe de Área Administrativa",
            },
        },
        "consumo_pico_excesivo": {
            "laboratorios": {
                "problema": f"Se detectaron {cantidad} eventos de consumo excesivo en horario pico en laboratorios de {sede}.",
                "causa": "Uso simultáneo de múltiples equipos de alto consumo.",
                "accion": "1. Escalonar uso de equipos de alto consumo\n2. Programar experimentos intensivos en horario valle\n3. Optimizar ocupación de laboratorios\n4. Identificar equipos con mayor demanda",
                "responsable": "Coordinador de Laboratorios",
            },
            "comedor": {
                "problema": f"Se detectaron {cantidad} eventos de consumo excesivo en horario pico en comedores de {sede}.",
                "causa": "Todos los equipos de cocción y refrigeración a máxima capacidad simultáneamente.",
                "accion": "1. Escalonar horarios de preparación de alimentos\n2. Precalentar equipos solo cuando sea necesario\n3. Optimizar distribución de carga eléctrica\n4. Evaluar capacidad vs demanda real",
                "responsable": "Administrador de Servicios Alimentarios",
            },
            "salones": {
                "problema": f"Se detectaron {cantidad} eventos de consumo excesivo en horario pico en salones de {sede}.",
                "causa": "Uso intensivo de iluminación y climatización.",
                "accion": "1. Optimizar temperatura de aires acondicionados (24-25°C)\n2. Aprovechar iluminación natural\n3. Apagar equipos en salones vacíos entre clases\n4. Sensores de ocupación",
                "responsable": "Servicios Generales",
            },
            "oficinas": {
                "problema": f"Se detectaron {cantidad} eventos de consumo excesivo en horario pico en oficinas de {sede}.",
                "causa": "Equipos de oficina y climatización operando simultáneamente.",
                "accion": "1. Configurar modo ahorro de energía en computadores\n2. Optimizar temperatura de aires acondicionados\n3. Apagar impresoras cuando no se usen\n4. Cerrar ventanas cuando AC está encendido",
                "responsable": "Jefe de Área Administrativa",
            },
        },
        "consumo_fuera_patron": {
            "laboratorios": {
                "problema": f"Se detectaron {cantidad} eventos de consumo atípico en laboratorios de {sede}.",
                "causa": "Uso irregular o eventos especiales no programados.",
                "accion": "1. Implementar sistema de registro de uso de laboratorios\n2. Analizar eventos atípicos caso por caso\n3. Protocolo de autorización para uso fuera de horario\n4. Monitoreo de consumo en tiempo real",
                "responsable": "Coordinador de Laboratorios",
            },
            "comedor": {
                "problema": f"Se detectaron {cantidad} eventos de consumo atípico en comedores de {sede}.",
                "causa": "Eventos especiales o preparación fuera de horario regular.",
                "accion": "1. Planificar eventos especiales con anticipación\n2. Optimizar preparación de alimentos\n3. Registro de eventos que generan consumo atípico\n4. Evaluar eficiencia energética en eventos",
                "responsable": "Administrador de Servicios Alimentarios",
            },
            "salones": {
                "problema": f"Se detectaron {cantidad} eventos de consumo atípico en salones de {sede}.",
                "causa": "Eventos académicos, conferencias o actividades extracurriculares.",
                "accion": "1. Centralizar eventos en salones específicos\n2. Programar eventos consecutivos en mismo lugar\n3. Apagar equipos inmediatamente al finalizar\n4. Capacitar organizadores sobre uso eficiente",
                "responsable": "Coordinación Académica",
            },
            "oficinas": {
                "problema": f"Se detectaron {cantidad} eventos de consumo atípico en oficinas de {sede}.",
                "causa": "Trabajo fuera de horario o reuniones no programadas.",
                "accion": "1. Habilitar áreas específicas para trabajo fuera de horario\n2. Desactivar climatización en áreas no ocupadas\n3. Sistema de registro de permanencia\n4. Iluminación localizada en vez de general",
                "responsable": "Jefe de Área Administrativa",
            },
        },
    }

    if tipo in recomendaciones_base and sector in recomendaciones_base[tipo]:
        recom = recomendaciones_base[tipo][sector]
        return recom["problema"], recom["causa"], recom["accion"], recom["responsable"]

    return (
        f"Consumo anómalo detectado en {sector} de {sede}.",
        "Causa por determinar mediante análisis detallado.",
        "Realizar auditoría energética específica del sector.",
        "Coordinador de Energía",
    )


def calcular_ahorro_potencial(row):
    desperdicio_total = row["desperdicio_total_kwh"]
    tipo = row["tipo_anomalia"]

    porcentaje_ahorro = {
        "consumo_nocturno_alto": 0.85,      # 85% (antes 80%)
        "consumo_fin_semana_alto": 0.80,    # 80% (antes 75%)
        "consumo_pico_excesivo": 0.40,      # 40% (antes 30%)
        "consumo_fuera_patron": 0.65,       # 65% (antes 40%)
    }

    factor = porcentaje_ahorro.get(tipo, 0.50)
    ahorro_kwh = desperdicio_total * factor

    costo_kwh = 700
    ahorro_cop_mes = (ahorro_kwh / 10) * costo_kwh

    return ahorro_kwh, ahorro_cop_mes


def calcular_dificultad_implementacion(row):
    tipo = row["tipo_anomalia"]
    sector = row["sector"]
    cantidad = row["cantidad_eventos"]

    dificultad_base = {
        "consumo_nocturno_alto": "MEDIA",
        "consumo_fin_semana_alto": "BAJA",
        "consumo_pico_excesivo": "ALTA",
        "consumo_fuera_patron": "MEDIA",
    }

    dificultad = dificultad_base.get(tipo, "MEDIA")

    if sector == "laboratorios" and tipo in ["consumo_nocturno_alto", "consumo_fin_semana_alto"]:
        dificultad = "ALTA"

    if cantidad > 20:
        if dificultad == "BAJA":
            dificultad = "MEDIA"
        elif dificultad == "MEDIA":
            dificultad = "ALTA"

    return dificultad


def generar_recomendaciones(df_patrones: pd.DataFrame) -> pd.DataFrame:
    print("Generando recomendaciones...")

    recomendaciones = []

    for idx, row in df_patrones.iterrows():
        problema, causa, accion, responsable = generar_recomendacion_texto(row)
        ahorro_kwh, ahorro_cop = calcular_ahorro_potencial(row)
        dificultad = calcular_dificultad_implementacion(row)

        recomendaciones.append({
            "prioridad": idx + 1,
            "sede": row["sede"],
            "sector": row["sector"],
            "tipo_anomalia": row["tipo_anomalia"],
            "cantidad_eventos": int(row["cantidad_eventos"]),
            "desperdicio_detectado_kwh": row["desperdicio_total_kwh"],
            "ahorro_potencial_kwh": round(ahorro_kwh, 2),
            "ahorro_mensual_cop": int(ahorro_cop),
            "problema": problema,
            "causa_probable": causa,
            "acciones_recomendadas": accion,
            "responsable": responsable,
            "dificultad_implementacion": dificultad,
            "eventos_criticos": int(row["eventos_criticos"]),
        })

    df_recomendaciones = pd.DataFrame(recomendaciones)

    print(f"Recomendaciones generadas: {len(df_recomendaciones)}")
    return df_recomendaciones


def priorizar_recomendaciones(df_recomendaciones: pd.DataFrame) -> pd.DataFrame:
    print("Priorizando recomendaciones...")

    pesos_dificultad = {
        "BAJA": 1.0,
        "MEDIA": 0.7,
        "ALTA": 0.4,
    }

    df_recomendaciones["peso_dificultad"] = df_recomendaciones["dificultad_implementacion"].map(pesos_dificultad)
    df_recomendaciones["score_priorizacion"] = (
        df_recomendaciones["ahorro_potencial_kwh"] *
        df_recomendaciones["peso_dificultad"]
    )

    df_recomendaciones = df_recomendaciones.sort_values("score_priorizacion", ascending=False)
    df_recomendaciones["prioridad_final"] = range(1, len(df_recomendaciones) + 1)

    df_recomendaciones = df_recomendaciones.drop(["peso_dificultad", "score_priorizacion"], axis=1)

    return df_recomendaciones


def mostrar_resumen(df_recomendaciones: pd.DataFrame) -> None:
    print("Resumen de recomendaciones")

    total_recomendaciones = len(df_recomendaciones)
    ahorro_total_kwh = df_recomendaciones["ahorro_potencial_kwh"].sum()
    ahorro_total_cop = df_recomendaciones["ahorro_mensual_cop"].sum()

    print(f"Total de recomendaciones: {total_recomendaciones}")
    print(f"Ahorro potencial total: {ahorro_total_kwh:.2f} kWh")
    print(f"Ahorro económico mensual: ${ahorro_total_cop:,} COP")
    print(f"Ahorro económico anual: ${ahorro_total_cop * 12:,} COP")

    print("Por dificultad de implementación:")
    print(df_recomendaciones["dificultad_implementacion"].value_counts())

    print("Por tipo de anomalía:")
    print(
        df_recomendaciones
        .groupby("tipo_anomalia")["ahorro_potencial_kwh"]
        .sum()
        .sort_values(ascending=False)
    )

    print("Por sede:")
    print(
        df_recomendaciones
        .groupby("sede")["ahorro_potencial_kwh"]
        .sum()
        .sort_values(ascending=False)
    )

    print("Top 10 recomendaciones prioritarias")
    top10 = df_recomendaciones.head(10)

    for _, row in top10.iterrows():
        print(f"{row['prioridad_final']}. {row['sede']} - {row['sector'].upper()}")
        print(f"   Tipo: {row['tipo_anomalia']}")
        print(f"   Ahorro: {row['ahorro_potencial_kwh']:.2f} kWh/mes (${row['ahorro_mensual_cop']:,} COP)")
        print(f"   Eventos: {row['cantidad_eventos']} ({row['eventos_criticos']} críticos)")
        print(f"   Dificultad: {row['dificultad_implementacion']}")


def guardar_recomendaciones(df_recomendaciones: pd.DataFrame) -> Path:
    carpeta_salidas = Path("outputs")
    carpeta_salidas.mkdir(exist_ok=True)

    ruta_salida = carpeta_salidas / "recomendaciones.csv"
    df_recomendaciones.to_csv(ruta_salida, index=False)

    print(f"Recomendaciones guardadas: {ruta_salida}")
    print(f"Total registros: {len(df_recomendaciones)}")

    return ruta_salida


def main() -> pd.DataFrame:
    print(f"Ejecutado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    df_anomalias = cargar_anomalias()
    df_patrones = agrupar_por_patron(df_anomalias)

    df_recomendaciones = generar_recomendaciones(df_patrones)
    df_recomendaciones = priorizar_recomendaciones(df_recomendaciones)

    mostrar_resumen(df_recomendaciones)
    guardar_recomendaciones(df_recomendaciones)

    print("Generación completada")
    return df_recomendaciones


if __name__ == "__main__":
    df_recomendaciones = main()
