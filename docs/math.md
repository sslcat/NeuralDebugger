# The mathematics I used

## Next-token prediction

I tokenize a chat transcript into indices $x_1,\ldots,x_T$. A causal language model factors its probability as

$$
p_\theta(x_{1:T})=\prod_{t=1}^{T} p_\theta(x_t\mid x_{<t}).
$$

A transformer block projects hidden states into queries, keys and values. One attention head computes

$$
A=\operatorname{softmax}\!\left(QK^\top/\sqrt{d_k}+M\right)V,
$$

where the causal mask $M$ gives future positions a logit of negative infinity. Attention mixes earlier token information. The output layer turns the final hidden state into vocabulary logits. Qwen supplies these pretrained blocks and embeddings.

## Supervised loss

For assistant target positions $S$, I minimize the mean negative log-likelihood

$$
L=-\frac1{|S|}\sum_{t\in S}\log \operatorname{softmax}(z_{t-1})_{x_t}.
$$

The logit at position $t-1$ predicts token $t$. The training encoder sets prompt labels to the ignore index $-100$. Transformers shifts the labels internally. I check that the prompt token IDs are an exact prefix of the full training transcript. Each microbatch contains one case. Gradient accumulation averages these per-case losses, so cases have equal weight even if their answer lengths differ.

## Backpropagation and optimization

For a composition $y=f(g(w))$, reverse-mode differentiation applies the chain rule to compute $\partial L/\partial w$. The simplest descent update is $w_{k+1}=w_k-\eta\nabla_wL$. My training loop uses AdamW, which maintains first and second moments of the gradient and applies decoupled weight decay. I divide each microbatch loss by the actual accumulation-group size and clip the resulting gradient norm to one before the update.

## Low-rank adaptation

For a frozen projection $W\in\mathbb R^{d_o\times d_i}$, the effective projection is

$$
W'=W+\frac{\alpha}{r}BA,\qquad A\in\mathbb R^{r\times d_i},\quad B\in\mathbb R^{d_o\times r}.
$$

Each adapted matrix adds $r(d_i+d_o)$ trainable parameters. I target query and value projections with rank 8 and scaling $\alpha=16$. The saved adapter holds learned factors. Inference reconstructs their effect alongside the pinned foundation weights. The transformer architecture stays the same.

## Quantization

For uniform affine quantization, a representative operation is $q=\mathrm{clip}(\mathrm{round}(w/s)+z)$, with reconstruction $\hat w=s(q-z)$, scale $s>0$, and zero point $z$. Quantization saves storage at the expense of rounding error. QLoRA can keep frozen weights in a blockwise 4-bit representation such as NF4 while training higher-precision adapters. The configured experiment uses ordinary LoRA with frozen floating-point base weights. The implementation does not perform integer quantization.

## Training, inference and scoring

During training I retain intermediate activations for differentiation. During inference I disable gradient recording and choose the highest-probability next token until the end marker or token cap.

For $N$ cases, top-level fix accuracy is $N^{-1}\sum_i \mathbf1[\text{all tests pass for }i]$. The test pass rate is $(\sum_i p_i)/(\sum_i n_i)$, where $p_i$ checks pass out of $n_i$. Category accuracy uses the same case average with an exact-match indicator. In the expanded and hybrid comparisons I average separate masked 0–2 semantic ratings for cause and explanation. The original pilot also reports lexical proxies. For a paired change I compute $m_{\rm adapter}-m_{\rm base}$. Relative change divides that difference by $m_{\rm base}$ when defined. I resample entire case pairs for uncertainty so a frequent input shape cannot masquerade as an independent program.
