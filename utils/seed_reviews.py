"""
seed_reviews.py — Gera e importa reviews mockados no ReviewPulse.

Uso:
    python seed_reviews.py                        # 500 reviews, configuração padrão
    python seed_reviews.py --total 5000           # 5000 reviews
    python seed_reviews.py --total 2000 --batch 200 --only-file  # só gera CSV, não importa
    python seed_reviews.py --email me@test.com --password secret

Dependências (stdlib apenas, sem pip):
    Python 3.8+
"""

import argparse
import csv
import json
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

BASE_URL = "http://localhost:8000/api"

DEFAULT_EMAIL = "admin@reviewpulse.com"
DEFAULT_PASSWORD = "admin123"
DEFAULT_TOTAL = 500
DEFAULT_BATCH = 100   # itens por request (a API processa async)

# ---------------------------------------------------------------------------
# Templates de reviews por categoria e sentimento
# ---------------------------------------------------------------------------

TEMPLATES = {
    "produto": {
        "positivo": [
            "Produto de excelente qualidade, superou minhas expectativas completamente.",
            "Chegou antes do prazo e embalagem impecável. Recomendo muito!",
            "Melhor custo-benefício que já encontrei nessa categoria.",
            "Exatamente como descrito. Produto perfeito, vou comprar de novo.",
            "Qualidade surpreendente pelo preço. Muito satisfeito com a compra.",
            "Material muito resistente e acabamento de primeira. Adorei!",
            "Produto bonito, funcional e durável. Valeu cada centavo.",
            "Muito bem construído. Dá para ver que tem qualidade nos materiais.",
        ],
        "negativo": [
            "Produto chegou com defeito de fábrica. Muito decepcionante.",
            "Qualidade bem abaixo do esperado pelo preço cobrado.",
            "Parou de funcionar após 2 semanas de uso. Péssima durabilidade.",
            "Material fraco, nada do que foi anunciado. Propaganda enganosa.",
            "Veio incompleto, faltando peças essenciais na caixa.",
            "Já está enferrujando com pouco tempo de uso. Produto ruim.",
            "Tamanho completamente diferente do indicado nas especificações.",
        ],
        "neutro": [
            "Produto ok, cumpre o que promete mas não tem nada de especial.",
            "Razoável para o preço, mas existem opções melhores no mercado.",
            "Funciona conforme esperado. Nem bom nem ruim.",
            "Entrega ok, produto ok. Nada que me impressionou ou decepcionou.",
        ],
    },
    "atendimento": {
        "positivo": [
            "Atendimento excepcional! Resolveram meu problema em menos de 10 minutos.",
            "Equipe muito prestativa e educada. Melhor suporte que já tive.",
            "Responderam rapidamente e resolveram minha dúvida completamente.",
            "Suporte proativo, me avisaram do problema antes mesmo de eu perceber.",
            "Atendente super paciente e explicou tudo de forma clara. Parabéns!",
            "Problema resolvido no primeiro contato. Muito eficiente!",
        ],
        "negativo": [
            "Esperei 3 dias por uma resposta e o problema não foi resolvido.",
            "Atendimento horrível, fui transferido 4 vezes e ninguém resolveu nada.",
            "Suporte completamente ineficaz. Tive que resolver o problema sozinho.",
            "Respostas automáticas sem nenhuma solução real. Péssimo!",
            "Chat offline às 14h de uma terça-feira. Horário de atendimento ridículo.",
            "Prometeram retorno em 24h, faz uma semana e nada. Abandono total.",
        ],
        "neutro": [
            "Atendimento ok, demorou um pouco mas resolveu no final.",
            "Suporte funcional, nada além do básico esperado.",
            "Resolveram o problema, mas o processo foi mais complicado do que devia.",
        ],
    },
    "entrega": {
        "positivo": [
            "Entrega relâmpago! Pediu hoje e chegou amanhã de manhã.",
            "Embalagem reforçada e produto chegou em perfeito estado.",
            "Enviaram com rastreamento detalhado. Sabia exatamente onde estava o pedido.",
            "Chegou dois dias antes do prazo estimado. Surpreendente!",
            "Entregador muito cuidadoso e gentil. Experiência excelente.",
        ],
        "negativo": [
            "Pedido perdido pelos Correios. Ninguém conseguiu localizar minha encomenda.",
            "Embalagem completamente amassada e produto danificado na entrega.",
            "Prazo era de 5 dias úteis, chegou em 18. Inaceitável.",
            "Tentaram entregar uma vez às 7h da manhã e não voltaram mais.",
            "Rastreamento parou de atualizar há uma semana. Sem informações.",
            "Entregaram na casa errada. Produto sumiu.",
        ],
        "neutro": [
            "Entrega dentro do prazo, nada além disso.",
            "Chegou ok, mas a embalagem deixou a desejar.",
            "Prazo cumprido, rastreamento funcionando. Entrega padrão.",
        ],
    },
    "app": {
        "positivo": [
            "Interface linda e muito intuitiva. Melhor app que uso no dia a dia.",
            "Funciona perfeitamente, nunca trava. Performance excelente.",
            "Atualização recente melhorou muito a velocidade. Parabéns à equipe!",
            "Design moderno e fluxo muito fácil de entender. Recomendo a todos.",
            "Onboarding perfeito, aprendi a usar o app em minutos.",
            "Notificações inteligentes que realmente fazem sentido.",
        ],
        "negativo": [
            "App trava toda vez que tento finalizar uma compra. Perco vendas por isso.",
            "Última atualização quebrou tudo. Voltei para a versão anterior.",
            "Consome bateria absurdamente mesmo em segundo plano.",
            "Botão de pagamento some aleatoriamente. Bug crítico sem correção.",
            "Carrega por mais de 30 segundos na tela inicial. Impossível usar.",
            "Dados desaparecem depois de fechar o app. Perdi todo meu histórico.",
            "Push notifications chegam com 2 horas de atraso. Inútil.",
        ],
        "neutro": [
            "App funcional mas interface desatualizada comparada aos concorrentes.",
            "Faz o que precisa, mas tem muito espaço para melhorar a UX.",
            "Estável na maioria do tempo, mas algumas telas poderiam ser mais rápidas.",
        ],
    },
    "preco": {
        "positivo": [
            "Preço justo pelo que entrega. Melhor custo-benefício da categoria.",
            "Promoção imperdível! Metade do preço com qualidade superior.",
            "Cobram pelo valor real que entregam. Muito honesto.",
            "Plano premium vale cada centavo. Retorno do investimento garantido.",
        ],
        "negativo": [
            "Preço absurdo para uma qualidade tão baixa. Não vale a pena.",
            "Cobram taxa de cancelamento sem deixar claro nos termos. Enganação.",
            "Aumentaram o preço em 40% sem nenhuma melhoria no serviço.",
            "Concorrentes entregam o mesmo por 30% menos. Sem justificativa.",
            "Cobrança duplicada no cartão. Suporte demorou dias para estornar.",
        ],
        "neutro": [
            "Preço dentro da média do mercado. Nem barato nem caro.",
            "Custo razoável, mas esperava mais pelo valor cobrado.",
        ],
    },
    "urgente": {
        "positivo": [],
        "negativo": [
            "URGENTE: sistema fora do ar em produção há 3 horas. Perda financeira real.",
            "Dados dos clientes possivelmente expostos. Preciso de resposta AGORA.",
            "Cobrança indevida de R$2.400 no meu cartão. Necessito estorno urgente.",
            "Pedido de casamento amanhã e o produto chegou errado. Emergência total.",
            "Sistema de pagamento travado. Não consigo processar nenhuma venda.",
            "Prazo contratual vence amanhã e o produto não chegou. Risco de multa.",
        ],
        "neutro": [],
    },
}

# Distribuição de sentimentos (deve somar 1.0)
SENTIMENT_DIST = {"positivo": 0.45, "negativo": 0.35, "neutro": 0.20}

# Distribuição de categorias
CATEGORY_WEIGHTS = {
    "produto":      0.28,
    "atendimento":  0.22,
    "entrega":      0.18,
    "app":          0.18,
    "preco":        0.10,
    "urgente":      0.04,
}

# ---------------------------------------------------------------------------
# Geração de reviews
# ---------------------------------------------------------------------------


def pick_sentiment() -> str:
    r = random.random()
    acc = 0.0
    for sentiment, weight in SENTIMENT_DIST.items():
        acc += weight
        if r < acc:
            return sentiment
    return "neutro"


def pick_category() -> str:
    r = random.random()
    acc = 0.0
    for cat, weight in CATEGORY_WEIGHTS.items():
        acc += weight
        if r < acc:
            return cat
    return "produto"


def generate_review(category: str, sentiment: str) -> str:
    pool = TEMPLATES[category][sentiment]
    if not pool:
        # fallback: pega de outra categoria com mesmo sentimento
        for cat in TEMPLATES:
            if TEMPLATES[cat][sentiment]:
                pool = TEMPLATES[cat][sentiment]
                break
    base = random.choice(pool)

    # pequenas variações para não repetir textos idênticos
    prefixes = [
        "", "", "",  # maioria sem prefixo
        "Honestamente, ", "Para ser sincero, ", "Na minha experiência, ",
        "Comprei semana passada e ", "Já sou cliente há anos: ",
    ]
    suffixes = [
        "", "", "",  # maioria sem sufixo
        " Recomendo.", " Não recomendo.", " Avalio com 5 estrelas.",
        " Decepcionado.", " Voltarei a comprar.", " Nunca mais compro aqui.",
    ]
    return random.choice(prefixes) + base + random.choice(suffixes)


def generate_batch(n: int) -> list[str]:
    reviews = []
    for _ in range(n):
        category = pick_category()
        sentiment = pick_sentiment()
        reviews.append(generate_review(category, sentiment))
    return reviews


# ---------------------------------------------------------------------------
# HTTP helpers (sem dependências externas)
# ---------------------------------------------------------------------------

def post_json(url: str, payload: dict, token: str | None = None) -> dict:
    data = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(
        url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(f"HTTP {e.code} — {body}") from e


def get_token(base_url: str, email: str, password: str) -> str:
    print(f"  Autenticando como {email}…")
    resp = post_json(f"{base_url}/auth/login/",
                     {"email": email, "password": password})
    token = resp.get("access")
    if not token:
        raise RuntimeError(f"Token não encontrado na resposta: {resp}")
    return token


# ---------------------------------------------------------------------------
# Exportação para arquivo
# ---------------------------------------------------------------------------

def save_txt(reviews: list[str], path: Path) -> None:
    path.write_text("\n".join(reviews) + "\n", encoding="utf-8")
    print(f"  TXT  salvo em: {path}  ({len(reviews)} linhas)")


def save_csv(reviews: list[str], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["text"])
        for r in reviews:
            writer.writerow([r])
    print(f"  CSV  salvo em: {path}  ({len(reviews)} linhas)")


def save_json(reviews: list[str], path: Path) -> None:
    path.write_text(json.dumps(reviews, ensure_ascii=False,
                    indent=2), encoding="utf-8")
    print(f"  JSON salvo em: {path}  ({len(reviews)} itens)")


# ---------------------------------------------------------------------------
# Importação via API
# ---------------------------------------------------------------------------

def import_reviews(
    reviews: list[str],
    base_url: str,
    token: str,
    batch_size: int,
) -> None:
    total = len(reviews)
    batches = [reviews[i: i + batch_size] for i in range(0, total, batch_size)]
    print(
        f"\n  Importando {total} reviews em {len(batches)} batches de {batch_size}…\n")

    for idx, batch in enumerate(batches, 1):
        try:
            resp = post_json(
                f"{base_url}/feedback-batches/",
                {"raw_text_list": batch},
                token=token,
            )
            batch_id = resp.get("batch_id", "?")
            print(
                f"  [{idx:>3}/{len(batches)}] ✓ batch_id={batch_id}  ({len(batch)} reviews)")
        except RuntimeError as e:
            print(f"  [{idx:>3}/{len(batches)}] ✗ Erro: {e}", file=sys.stderr)

        # respeita o rate limit do Celery worker
        if idx < len(batches):
            time.sleep(0.3)

    print(f"\n  Importação concluída: {total} reviews enviados.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Gera e importa reviews mockados no ReviewPulse."
    )
    p.add_argument("--total",     type=int,  default=DEFAULT_TOTAL,
                   help="Total de reviews a gerar (default: 500)")
    p.add_argument("--batch",     type=int,  default=DEFAULT_BATCH,
                   help="Reviews por request à API (default: 100)")
    p.add_argument("--base-url",  type=str,  default=BASE_URL,
                   help=f"URL base da API (default: {BASE_URL})")
    p.add_argument("--email",     type=str,
                   default=DEFAULT_EMAIL,    help="E-mail de login")
    p.add_argument("--password",  type=str,
                   default=DEFAULT_PASSWORD, help="Senha de login")
    p.add_argument("--only-file", action="store_true",
                   help="Só gera os arquivos, não importa via API")
    p.add_argument("--seed",      type=int,  default=None,
                   help="Seed para reprodutibilidade (ex: --seed 42)")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    if args.seed is not None:
        random.seed(args.seed)
        print(f"  Seed: {args.seed}")

    print(f"\n{'='*55}")
    print(f"  ReviewPulse — seed_reviews.py")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*55}")
    print(f"  Total de reviews : {args.total}")
    print(f"  Batch size       : {args.batch}")
    print(
        f"  Destino          : {'apenas arquivos' if args.only_file else args.base_url}")
    print(f"{'='*55}\n")

    # 1. Gera os dados
    print("  Gerando reviews…")
    reviews = generate_batch(args.total)
    print(f"  {len(reviews)} reviews gerados.\n")

    # 2. Salva arquivos locais dentro de reviews/
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(__file__).parent / "reviews"
    out_dir.mkdir(exist_ok=True)
    print(f"  Pasta de saída: {out_dir}\n")
    save_txt(reviews,  out_dir / f"reviews_{ts}.txt")
    save_csv(reviews,  out_dir / f"reviews_{ts}.csv")
    save_json(reviews, out_dir / f"reviews_{ts}.json")

    if args.only_file:
        print("\n  --only-file ativo: importação pulada.")
        return

    # 3. Autentica e importa
    print()
    try:
        token = get_token(args.base_url, args.email, args.password)
    except RuntimeError as e:
        print(f"\n  ✗ Falha na autenticação: {e}", file=sys.stderr)
        print("  Dica: use --email e --password, ou --only-file para só gerar os arquivos.")
        sys.exit(1)

    import_reviews(reviews, args.base_url, token, args.batch)


if __name__ == "__main__":
    main()

    # Só gerar os arquivos (sem precisar da API no ar)
    # python seed_reviews.py --only-file

    # Gerar E importar direto na API (Docker deve estar rodando)
    # python seed_reviews.py --email seu@email.com --password suasenha

    # Mais volume
    # python seed_reviews.py --total 5000 --email seu@email.com --password suasenha
