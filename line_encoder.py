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


def hdb3(bits: list[int]) -> list[int]:
    """HDB3 (High Density Bipolar 3):
       Extension of AMI — runs of 4 consecutive zeros are replaced by
       a special substitution pattern to avoid long zero runs.
       Substitution depends on:
         - parity of preceding 1-pulses (even/odd)
         - polarity of last transmitted pulse
       Pattern B00V  (odd count)  or  000V / B00V  (even count).
    """
    result = [0] * len(bits)
    last_polarity = 1     # polarity of last non-zero AMI pulse
    pulse_count   = 0     # count of +1/-1 pulses sent so far

    i = 0
    while i < len(bits):
        # detect a run of 4 zeros starting at i
        if (bits[i] == 0
                and i + 3 < len(bits)
                and bits[i+1] == 0
                and bits[i+2] == 0
                and bits[i+3] == 0):

            v = last_polarity          # violation pulse — same polarity as last
            if pulse_count % 2 == 0:
                # even number of pulses since last substitution → B00V
                b = -last_polarity     # balancing pulse — opposite polarity
                result[i]   = b
                result[i+1] = 0
                result[i+2] = 0
                result[i+3] = v
                last_polarity = v
                pulse_count += 2       # B and V both count
            else:
                # odd → 000V
                result[i]   = 0
                result[i+1] = 0
                result[i+2] = 0
                result[i+3] = v
                last_polarity = v
                pulse_count += 1       # only V counts
            i += 4
        else:
            if bits[i] == 1:
                result[i]     = last_polarity
                last_polarity = -last_polarity
                pulse_count  += 1
            else:
                result[i] = 0
            i += 1

    return result


def mlt3(bits: list[int]) -> list[int]:
    """MLT-3 (Multi-Level Transmit 3):
       Signal cycles through levels +1 → 0 → -1 → 0 → +1 …
       on each 1-bit.  0-bits cause no change.
       Sequence: +1, 0, -1, 0, +1, 0, -1, 0 …
    """
    sequence = [1, 0, -1, 0]   # repeating cycle
    result   = []
    state    = 0               # index into sequence

    for b in bits:
        if b == 1:
            state = (state + 1) % 4
        result.append(sequence[state])

    return result


# 4B/5B lookup table — every 4-bit nibble maps to a 5-bit code
_4B5B_TABLE = {
    '0000': '11110', '0001': '01001', '0010': '10100', '0011': '10101',
    '0100': '01010', '0101': '01011', '0110': '01110', '0111': '01111',
    '1000': '10010', '1001': '10011', '1010': '10110', '1011': '10111',
    '1100': '11010', '1101': '11011', '1110': '11100', '1111': '11101',
}

def four_b_five_b(bits: list[int]) -> list[int]:
    """4B/5B block encoding:
       Pads input to a multiple of 4, maps each 4-bit group to its
       5-bit code word (guarantees ≤ 3 consecutive zeros).
       The resulting bit stream is then NRZ-I encoded for the final signal.
    """
    # pad to multiple of 4
    padded = bits[:]
    if len(padded) % 4:
        padded += [0] * (4 - len(padded) % 4)

    encoded_bits = []
    for i in range(0, len(padded), 4):
        nibble = ''.join(str(b) for b in padded[i:i+4])
        encoded_bits += [int(x) for x in _4B5B_TABLE[nibble]]

    # NRZ-I on the 5-bit codes (standard pairing for 4B/5B)
    return nrz_i(encoded_bits)


# ── public API ────────────────────────────────────────────────────────────────

ENCODERS = {
    'nrz_l':                  ('NRZ-L',                   nrz_l),
    'nrz_i':                  ('NRZ-I',                   nrz_i),
    'manchester':             ('Manchester',               manchester),
    'differential_manchester': ('Differential Manchester', differential_manchester),
    'ami':                    ('AMI',                     ami),
    'hdb3':                   ('HDB3',                    hdb3),
    'mlt3':                   ('MLT-3',                   mlt3),
    'four_b_five_b':          ('4B/5B',                   four_b_five_b),
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