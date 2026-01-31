
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

def cargar_predicciones():
    # Cargar archivo de predicciones generado por el modelo
    rutas_posibles = [
        "notebooks/outputs/predicciones_2025.csv",
        "outputs/predicciones_2025.csv"
    ]

    ruta_encontrada = None
    for ruta in rutas_posibles:
        if Path(ruta).exists():
            ruta_encontrada = ruta
            break

    if ruta_encontrada is None:
        raise FileNotFoundError(
            "No se encontró el archivo predicciones_2025.csv. "
            "Ejecuta primero el entrenamiento del modelo."
        )

    df_predicciones = pd.read_csv(ruta_encontrada)
    df_predicciones["timestamp"] = pd.to_datetime(df_predicciones["timestamp"])

    print(f"Predicciones cargadas desde: {ruta_encontrada}")
    print(f"Registros: {len(df_predicciones)}")

    return df_predicciones


def calcular_diferencias(df_predicciones):
    # Calcular diferencias entre valores reales y predichos
    sectores = ["comedor", "salones", "laboratorios", "auditorios", "oficinas"]

    for sector in sectores:
        columna_real = f"{sector}_real"
        columna_pred = f"{sector}_pred"

        df_predicciones[f"{sector}_diff"] = df_predicciones[columna_real] - df_predicciones[columna_pred]

        df_predicciones[f"{sector}_diff_pct"] = np.where(
            df_predicciones[columna_pred] > 0,
            (df_predicciones[f"{sector}_diff"] / df_predicciones[columna_pred]) * 100,
            0
        )

    df_predicciones["total_diff"] = df_predicciones["total_real"] - df_predicciones["total_pred"]
    df_predicciones["total_diff_pct"] = np.where(
        df_predicciones["total_pred"] > 0,
        (df_predicciones["total_diff"] / df_predicciones["total_pred"]) * 100,
        0
    )

    print("Diferencias calculadas")

    return df_predicciones


def detectar_anomalias(df_predicciones, umbral_moderado=1.15, umbral_critico=1.30):
    # Detectar anomalías comparando real vs predicción
    anomalias = []
    sectores = ["comedor", "salones", "laboratorios", "oficinas"]

    for _, fila in df_predicciones.iterrows():
        for sector in sectores:
            valor_real = fila[f"{sector}_real"]
            valor_pred = fila[f"{sector}_pred"]

            if valor_real > 0.5 and valor_pred > 0:
                ratio = valor_real / valor_pred

                if ratio >= umbral_critico:
                    severidad = "critica"
                elif ratio >= umbral_moderado:
                    severidad = "moderada"
                else:
                    continue

                hora = fila["hora"]
                dia_semana = fila["dia_semana"]

                if hora in [0, 1, 2, 3, 4, 5, 6]:
                    tipo = "consumo_nocturno_alto"
                elif dia_semana in [5, 6]:
                    tipo = "consumo_fin_semana_alto"
                elif hora in [7, 8, 9, 10, 11, 14, 15, 16, 17]:
                    tipo = "consumo_pico_excesivo"
                else:
                    tipo = "consumo_fuera_patron"

                anomalias.append({
                    "timestamp": fila["timestamp"],
                    "sede": fila["sede"],
                    "sector": sector,
                    "hora": hora,
                    "dia_semana": dia_semana,
                    "real_kwh": valor_real,
                    "esperado_kwh": valor_pred,
                    "diferencia_kwh": valor_real - valor_pred,
                    "diferencia_pct": ((valor_real - valor_pred) / valor_pred) * 100,
                    "ratio": ratio,
                    "severidad": severidad,
                    "tipo_anomalia": tipo
                })

    df_anomalias = pd.DataFrame(anomalias)

    print(f"Anomalías detectadas: {len(df_anomalias)}")

    if not df_anomalias.empty:
        print("Por severidad:")
        print(df_anomalias["severidad"].value_counts())
        print("Por sector:")
        print(df_anomalias["sector"].value_counts())

    return df_anomalias


def analizar_por_sede_sector(df_anomalias):
    # Resumen de anomalías por sede y sector
    if df_anomalias.empty:
        print("No hay anomalías para analizar")
        return None

    resumen = df_anomalias.groupby(["sede", "sector"]).agg(
        cantidad_anomalias=("diferencia_kwh", "count"),
        total_desperdicio_kwh=("diferencia_kwh", "sum"),
        promedio_desperdicio_kwh=("diferencia_kwh", "mean"),
        anomalias_criticas=("severidad", lambda x: (x == "critica").sum())
    ).round(2)

    resumen = resumen.sort_values("total_desperdicio_kwh", ascending=False)

    print("Resumen por sede y sector:")
    print(resumen.head(10))

    return resumen


def top_anomalias_criticas(df_anomalias, n=20):
    # Mostrar anomalías críticas más grandes
    if df_anomalias.empty:
        return None

    criticas = df_anomalias[df_anomalias["severidad"] == "critica"]
    criticas = criticas.sort_values("diferencia_kwh", ascending=False).head(n)

    for i, fila in criticas.iterrows():
        print(f"{fila['timestamp']} - {fila['sede']} - {fila['sector']}")
        print(f"Real: {fila['real_kwh']:.2f} | Esperado: {fila['esperado_kwh']:.2f}")
        print(f"Exceso: {fila['diferencia_kwh']:.2f} kWh")

    return criticas


def guardar_anomalias(df_anomalias):
    # Guardar anomalías en archivo CSV
    if df_anomalias.empty:
        print("No hay anomalías para guardar")
        return

    Path("data/outputs").mkdir(parents=True, exist_ok=True)
    ruta_salida = "data/outputs/anomalias.csv"

    df_anomalias.to_csv(ruta_salida, index=False)

    print(f"Anomalías guardadas en: {ruta_salida}")
    print(f"Total registros: {len(df_anomalias)}")

    ahorro_total = df_anomalias["diferencia_kwh"].sum()
    ahorro_estimado = ahorro_total * 700

    print(f"Ahorro potencial detectado: {ahorro_total:.2f} kWh")
    print(f"Ahorro económico estimado: ${ahorro_estimado:,.0f} COP")


def main():
    print(f"Detector de anomalías ejecutado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    df_predicciones = cargar_predicciones()
    df_predicciones = calcular_diferencias(df_predicciones)

    df_anomalias = detectar_anomalias(
        df_predicciones,
        umbral_moderado=1.15,
        umbral_critico=1.30
    )

    resumen = analizar_por_sede_sector(df_anomalias)
    top_anomalias_criticas(df_anomalias, n=20)
    guardar_anomalias(df_anomalias)

    return df_anomalias, resumen


if __name__ == "__main__":
    df_anomalias, resumen = main()
