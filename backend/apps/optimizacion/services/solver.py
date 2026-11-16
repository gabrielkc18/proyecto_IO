
import pulp


def resolver_problema(productos, recursos, sentido_objetivo="MAX"):
    """
    Resuelve un problema de optimización de producción entera.

    productos:
        [
            {
                "codigo": "P1",
                "utilidad_unitaria": 80
            }
        ]

    recursos:
        [
            {
                "nombre": "Materia A",
                "disponibilidad": 3000,
                "consumos": {
                    "P1": 4
                }
            }
        ]

    sentido_objetivo: MAX o MIN
    """

    # 1. Validar datos básicos
    if not productos:
        raise ValueError("Debe existir al menos un producto.")

    if not recursos:
        raise ValueError("Debe existir al menos un recurso.")

    if sentido_objetivo not in ("MAX", "MIN"):
        raise ValueError("El sentido debe ser MAX o MIN.")

    codigos = [p["codigo"] for p in productos]

    if len(codigos) != len(set(codigos)):
        raise ValueError("Los códigos de productos deben ser únicos.")

    nombres_recursos = [r["nombre"] for r in recursos]

    if len(nombres_recursos) != len(set(nombres_recursos)):
        raise ValueError("Los nombres de recursos deben ser únicos.")

    for producto in productos:
        utilidad = producto["utilidad_unitaria"]

        if utilidad < 0:
            raise ValueError("La utilidad no puede ser negativa.")

    for recurso in recursos:
        if recurso["disponibilidad"] < 0:
            raise ValueError("La disponibilidad no puede ser negativa.")

        for cantidad in recurso["consumos"].values():
            if cantidad < 0:
                raise ValueError("Los consumos no pueden ser negativos.")

    # 2. Crear el modelo matemático
    sentido = (
        pulp.LpMaximize
        if sentido_objetivo == "MAX"
        else pulp.LpMinimize
    )

    modelo = pulp.LpProblem("PlanificaIO", sentido)

    # 3. Crear variables de decisión enteras
    variables = {
        producto["codigo"]: modelo.add_variable(
            name=f"x_{producto['codigo']}",
            lowBound=0,
            cat="Integer"
        )
        for producto in productos
    }

    # 4. Construir la función objetivo
    modelo += pulp.lpSum(
        producto["utilidad_unitaria"] * variables[producto["codigo"]]
        for producto in productos
    )

    # 5. Construir las restricciones de recursos
    for recurso in recursos:
        consumo_total = pulp.lpSum(
            recurso["consumos"].get(producto["codigo"], 0)
            * variables[producto["codigo"]]
            for producto in productos
        )

        modelo += consumo_total <= recurso["disponibilidad"]

    # 6. Ejecutar el solver
    stats = modelo.solve(pulp.COIN_CMD(msg=False))

    estado = stats.status_str

    resultado = {
        "estado": estado,
        "sentido_objetivo": sentido_objetivo,
        "utilidad_total": None,
        "productos": [],
        "recursos": [],
    }

    # 7. Interpretar el resultado
    if estado != "Optimal":
        return resultado

    resultado["utilidad_total"] = pulp.value(modelo.objective)

    # Resultados por producto
    for producto in productos:
        cantidad = pulp.value(variables[producto["codigo"]])

        resultado["productos"].append({
            "codigo": producto["codigo"],
            "cantidad": int(round(cantidad)),
            "utilidad_unitaria": producto["utilidad_unitaria"],
            "utilidad_aportada": (
                producto["utilidad_unitaria"] * int(round(cantidad))
            ),
        })

    # Resultados por recurso
    for recurso in recursos:
        consumo_total = sum(
            recurso["consumos"].get(producto["codigo"], 0)
            * pulp.value(variables[producto["codigo"]])
            for producto in productos
        )

        holgura = recurso["disponibilidad"] - consumo_total

        resultado["recursos"].append({
            "nombre": recurso["nombre"],
            "disponibilidad": recurso["disponibilidad"],
            "consumo_total": consumo_total,
            "holgura": holgura,
            "estado_uso": (
                "AGOTADO" if abs(holgura) < 1e-7 else "CON_HOLGURA"
            ),
        })

    return resultado
