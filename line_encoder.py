import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io, base64


# ── helpers ──────────────────────────────────────────────────────────────────

def _plot_to_b64(signal, title, color='#00c896'):
    """Render a step-plot and return a base-64 PNG string."""
    fig, ax = plt.subplots(figsize=(9, 2.6))
    fig.patch.set_facecolor('#0d0d0d')
    ax.set_facecolor('#0d0d0d')

    ax.plot(signal, color=color, linewidth=2, drawstyle='steps-pre')
    ax.axhline(0, color='#333', linewidth=0.8)
    ax.set_title(title, color='#e0e0e0', fontsize=12, pad=8)
    ax.tick_params(colors='#555')
    for spine in ax.spines.values():
        spine.set_edgecolor('#222')
    ax.set_ylim(-1.6, 1.6)
    ax.set_yticks([-1, 0, 1])
    ax.set_yticklabels(['-1', '0', '+1'], color='#777')
    ax.set_xticks([])

    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png', dpi=120, facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


def _validate(data: str):
    """Raise ValueError if data is not a non-empty binary string."""
    if not data:
        raise ValueError("Input cannot be empty.")
    if any(c not in '01' for c in data):
        raise ValueError("Input must contain only 0s and 1s.")


# ── encoders ─────────────────────────────────────────────────────────────────

def nrz_l(bits: list[int]) -> list[int]:
    """NRZ-L: 0 → +1,  1 → -1"""
    return [1 if b == 0 else -1 for b in bits]


def nrz_i(bits: list[int]) -> list[int]:
    """NRZ-I: transition on 1, no transition on 0."""
    result = []
    current = 1          # start high
    for b in bits:
        if b == 1:
            current = -current   # transition
        result.append(current)
    return result


def manchester(bits: list[int]) -> list[int]:
    """Manchester: 0 → low-to-high (+1 then -1 … wait, IEEE 802.3)
       Using IEEE 802.3 convention: 0 → -1,+1  |  1 → +1,-1
    """
    result = []
    for b in bits:
        if b == 0:
            result += [-1, 1]
        else:
            result += [1, -1]
    return result


def differential_manchester(bits: list[int]) -> list[int]:
    """Differential Manchester:
       - Always a transition in the middle of each bit period.
       - 0 → transition at START of period.
       - 1 → no transition at start of period.
    """
    result = []
    current = 1          # level at start of first period

    for b in bits:
        if b == 0:
            current = -current          # transition at start
        first_half  = current
        second_half = -current          # mid-bit transition always
        result += [first_half, second_half]
        current = second_half

    return result


def ami(bits: list[int]) -> list[int]:
    """AMI: 0 → 0,  1 → alternating +1 / -1"""
    result = []
    polarity = 1
    for b in bits:
        if b == 0:
            result.append(0)
        else:
            result.append(polarity)
            polarity = -polarity
    return result


# ── public API ────────────────────────────────────────────────────────────────

ENCODERS = {
    'nrz_l':                 ('NRZ-L',                  nrz_l),
    'nrz_i':                 ('NRZ-I',                  nrz_i),
    'manchester':            ('Manchester',              manchester),
    'differential_manchester':('Differential Manchester', differential_manchester),
    'ami':                   ('AMI',                    ami),
}


def encode_and_plot(data: str, scheme: str):
    """
    Validate input, run chosen encoder, return two base-64 PNG strings.
    Returns: (original_img_b64, encoded_img_b64, title)
    """
    _validate(data)
    if scheme not in ENCODERS:
        raise ValueError(f"Unknown encoding scheme: {scheme}")

    bits = [int(c) for c in data]
    label, fn = ENCODERS[scheme]

    original_signal = [0] + bits          # prepend 0 so steps look clean
    encoded_signal  = fn(bits)

    orig_img = _plot_to_b64(original_signal, 'Original Data',    color='#4a9eff')
    enc_img  = _plot_to_b64(encoded_signal,  f'Encoded — {label}', color='#00c896')

    return orig_img, enc_img, label