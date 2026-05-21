export async function uploadBatch(
  body: FormData | { raw_text_list: string[] },
) {
  const isFile = body instanceof FormData;

  const res = await fetch("/api/feedback-batches/", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${getToken()}`,
      // Não setar Content-Type para FormData — o browser define o boundary
      ...(isFile ? {} : { "Content-Type": "application/json" }),
    },
    body: isFile ? body : JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.error ?? "Erro desconhecido");
  }
  return res.json();
}
