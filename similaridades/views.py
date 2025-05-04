import re
import pandas as pd
import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from nltk.tokenize import word_tokenize

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.generics import CreateAPIView

from django.core.paginator import Paginator
from django.contrib.auth.models import User

from .models import TextoEvento
from .serializers import TextoInputSerializer, TextEventSerializer
from io import StringIO


class SimilaridadeView(APIView):
    def get(self, request):
        return Response(
            {
                "mensagem": "Bem-vindo à API de Similaridade de Textos!",
                "uso": {
                    "metodo": "POST",
                    "endpoint": "/api/similaridade/",
                    "descricao": "Envie uma lista de objetos com 'descricao' e 'evento' para obter similaridade",
                    "exemplo": [
                        {"descricao": "texto exemplo", "evento": "Evento em 2022"},
                        {"descricao": "texto semelhante", "evento": "Evento em 2021"},
                    ],
                },
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        serializer = TextoInputSerializer(data=request.data, many=True)
        if serializer.is_valid():
            data = serializer.validated_data
            new_df = pd.DataFrame(data)

            textos_banco = TextoEvento.objects.all().values(
                "descricao", "evento", "ano"
            )
            db_df = pd.DataFrame(list(textos_banco))

            if not db_df.empty:
                new_df["origem"] = "requisicao"
                db_df["origem"] = "banco"

                combined_df = pd.concat([new_df, db_df], ignore_index=True)
            else:
                combined_df = new_df.copy()
                combined_df["origem"] = "requisicao"

            combined_df["descricao"] = combined_df["descricao"].apply(
                lambda x: word_tokenize(x.lower())
            )
            combined_df["descricao"] = combined_df["descricao"].apply(
                lambda x: [word for word in x if word.isalnum()]
            )

            # Transformar para o formato adequado para o TF-IDF
            results = combined_df["descricao"].apply(lambda x: " ".join(map(str, x)))
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform(results)

            saida = []

            indices_requisicao = combined_df[
                combined_df["origem"] == "requisicao"
            ].index

            for idx in indices_requisicao:
                try:
                    ano_evento = re.search(
                        r"\d{4}", combined_df["evento"].iloc[idx]
                    ).group()[:4]
                except AttributeError:
                    ano_evento = None

                similaridade_linear = linear_kernel(
                    tfidf_matrix[idx : idx + 1], tfidf_matrix
                ).flatten()

                # Filtrar textos do mesmo ano
                for j in range(len(combined_df)):
                    if ano_evento and re.search(
                        r"\d{4}", combined_df["evento"].iloc[j]
                    ):
                        if (
                            re.search(r"\d{4}", combined_df["evento"].iloc[j]).group()[
                                :4
                            ]
                            == ano_evento
                        ):
                            similaridade_linear[j] = 0

                # Não comparar o texto consigo mesmo
                similaridade_linear[idx] = 0

                most_similar = np.argmax(similaridade_linear)
                most_similar_value = float(similaridade_linear[most_similar])

                saida.append(
                    {
                        "texto_base": combined_df["descricao"].iloc[idx],
                        "evento_base": combined_df["evento"].iloc[idx],
                        "texto_mais_semelhante": combined_df["descricao"].iloc[
                            most_similar
                        ],
                        "evento_mais_semelhante": combined_df["evento"].iloc[
                            most_similar
                        ],
                        "origem_texto_similar": combined_df["origem"].iloc[
                            most_similar
                        ],
                        "similaridade": most_similar_value,
                    }
                )

            return Response(saida, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TextEventView(APIView):
    queryset = TextoEvento.objects.all()
    serializer_class = TextEventSerializer

    def get_permissions(self):
        """
        Define permissões:
        - GET é acessível a todos
        - POST, PUT, DELETE requerem autenticação
        """
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, pk=None):
        """Lista eventos com opções de filtro por ano ou nome do evento."""
        if pk is not None:
            try:
                evento = TextoEvento.objects.get(pk=pk)
                serializer = TextEventSerializer(evento)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except TextoEvento.DoesNotExist:
                return Response(
                    {"error": "Evento não encontrado"}, status=status.HTTP_404_NOT_FOUND
                )

        eventos = TextoEvento.objects.all()

        ano = request.query_params.get("ano", None)
        if ano:
            eventos = eventos.filter(ano=ano)

        nome_evento = request.query_params.get("evento", None)
        if nome_evento:
            eventos = eventos.filter(evento__icontains=nome_evento)

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 10))

        paginator = Paginator(eventos, page_size)
        eventos_paginados = paginator.get_page(page)

        serializer = TextEventSerializer(eventos_paginados, many=True)

        print("Modelo raw data:", list(eventos_paginados))
        print("Serializer data:", serializer.data)

        return Response(
            {
                "total": paginator.count,
                "pages": paginator.num_pages,
                "current_page": int(page),
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """Cria um novo evento usando um arquivo csv que for enviado para essa rota."""
        if "file" not in request.FILES:
            return Response(
                {"error": "Nenhum arquivo CSV enviado"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        csv_file = request.FILES["file"]
        if not csv_file.name.endswith(".csv"):
            return Response(
                {"error": "Arquivo deve ser CSV"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            file_data = csv_file.read().decode("utf-8")
            df = pd.read_csv(StringIO(file_data))

            print(df.head())  # Debug: Verifique os dados lidos do CSV

            required_columns = ["evento", "descricao", "ano"]
            for col in required_columns:
                if col not in df.columns:
                    return Response(
                        {"error": f"Coluna {col} não encontrada no CSV"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # Importar dados
            created_count = 0
            for _, row in df.iterrows():
                TextoEvento.objects.create(
                    descricao=row["descricao"], evento=row["evento"], ano=row["ano"]
                )
                created_count += 1

            return Response(
                {"success": f"Importados {created_count} registros com sucesso"},
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response(
                {"error": f"Erro ao processar o arquivo: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def put(self, request, pk):
        """Atualiza um evento existente."""
        try:
            evento = TextoEvento.objects.get(pk=pk)
        except TextoEvento.DoesNotExist:
            return Response(
                {"error": "Evento não encontrado"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = TextEventSerializer(evento, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None):
        if pk is None:
            TextoEvento.objects.all().delete()
            return Response(
                {"success": "Todos os eventos deletados com sucesso"},
                status=status.HTTP_204_NO_CONTENT,
            )
        else:
            try:
                evento = TextoEvento.objects.get(pk=pk)
                evento.delete()
                return Response(
                    {"success": "Evento deletado com sucesso"},
                    status=status.HTTP_204_NO_CONTENT,
                )
            except TextoEvento.DoesNotExist:
                return Response(
                    {"error": "Evento não encontrado"}, status=status.HTTP_404_NOT_FOUND
                )
