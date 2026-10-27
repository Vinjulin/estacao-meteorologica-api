# API #

import os
from datetime import datetime
from typing import Optional

import psycopg
from psycopg.rows import dict_row
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="API da Estacao Meteorologica")

DATABASE_URL = os.getenv("DATABASE_URL")


def conectar():
    if not DATABASE_URL:
        raise RuntimeError(
            "A variavel DATABASE_URL nao foi configurada."
        )

    return psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row,
        connect_timeout=10
    )


class Medicao(BaseModel):
    temperatura: Optional[float] = None
    umidade: Optional[float] = None
    pressao_hpa: Optional[float] = None
    luminosidade: Optional[int] = None
    mq2_adc: Optional[int] = None
    chuva_mm: Optional[float] = None


@app.get("/")
def inicio():
    return {
        "mensagem": "API da Estacao Meteorologica funcionando!"
    }


@app.get("/teste-banco")
def teste_banco():
    try:
        with conectar() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT NOW() AS horario")
                resultado = cursor.fetchone()

        return {
            "mensagem": "Conexao com o Neon funcionando!",
            "horario_banco": resultado["horario"]
        }

    except Exception as erro:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao conectar ao banco: {str(erro)}"
        )


@app.post("/medicoes")
def criar_medicao(medicao: Medicao):
    try:
        with conectar() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO medicoes (
                        temperatura,
                        umidade,
                        pressao_hpa,
                        luminosidade,
                        mq2_adc,
                        chuva_mm
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    (
                        medicao.temperatura,
                        medicao.umidade,
                        medicao.pressao_hpa,
                        medicao.luminosidade,
                        medicao.mq2_adc,
                        medicao.chuva_mm
                    )
                )
                resultado = cursor.fetchone()

        return {
            "mensagem": "Medicao salva com sucesso!",
            "medicao": resultado
        }

    except Exception as erro:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao salvar medicao: {str(erro)}"
        )


@app.get("/medicoes")
@app.get("/publico/medicoes")
def listar_medicoes():
    try:
        with conectar() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        id,
                        data_hora,
                        temperatura,
                        umidade,
                        pressao_hpa,
                        luminosidade,
                        mq2_adc,
                        chuva_mm
                    FROM medicoes
                    ORDER BY id DESC
                    LIMIT 1000
                    """
                )
                medicoes = cursor.fetchall()

        return {
            "total": len(medicoes),
            "medicoes": medicoes
        }

    except Exception as erro:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao consultar medicoes: {str(erro)}"
        )
