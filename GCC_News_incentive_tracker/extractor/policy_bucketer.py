import re


class PolicyBucketer:

    INCENTIVE_TYPES = [
        "Financial Incentives",
        "Infrastructure",
        "Talent",
        "Regulatory, Ease-of-Doing-Business & Non-financial Support",
        "Innovation / R&D / Patent",
        "Others",
    ]

    SCOPES = [
        "Across the state (Common)",
        "Specific to Tier 1 cities",
        "Specific to Tier 2 & 3 cities",
    ]

    KEYWORD_MAP = {
        "Financial Incentives": [
            # English
            "capex", "opex", "capital subsidy", "capital support",
            "capital incentive", "stamp duty", "registration fee",
            "interest subsidy", "interest assistance", "tax exemption",
            "tax holiday", "sgst", "vat", "income tax", "payroll subsidy",
            "financial assistance", "fiscal incentive", "reimbursement of",
            "concession", "subsidy", "grant", "tax credit", "tax relief",
            "withholding tax",
            # Spanish
            "subsidio", "subvención", "exención fiscal", "deducción fiscal",
            "crédito fiscal", "reembolso", "bonificación", "exoneración",
            "impuesto sobre la renta", "isr", "iva", "itbis",
            "incentivo fiscal", "beneficio fiscal", "reducción impositiva",
            "estímulo fiscal", "exento", "tasa cero",
        ],
        "Infrastructure": [
            # English
            "electricity duty", "power tariff", "land subsidy", "land rebate",
            "land cost", "rental subsidy", "lease rental", "rental assistance",
            "bandwidth", "internet", "cloud rental", "gcc park", "it park",
            "gift city", "infrastructure", "right of way", "fibre", "fiber",
            "co-working", "office space", "industrial estate", "data centre",
            "data center", "plug and play", "broadband",
            # Spanish
            "zona económica", "zona franca", "parque industrial",
            "infraestructura", "electricidad", "energía", "banda ancha",
            "oficina", "alquiler", "arrendamiento", "suelo", "terreno",
            "telecomunicaciones",
        ],
        "Talent": [
            # English
            "skilling", "training", "internship", "academia", "upskill",
            "atmanirbhar", "rojgar", "employee provident fund",
            "employees' provident fund", "epf", "employment generation",
            "recruitment", "talent", "workforce", "human capital",
            # Spanish
            "capacitación", "formación", "empleo", "trabajador",
            "contratación", "recursos humanos", "fuerza laboral",
            "talento", "educación", "pasantía",
        ],
        "Regulatory, Ease-of-Doing-Business & Non-financial Support": [
            # English
            "single window", "single-window", "clearance", "regulatory",
            "compliance", "deemed approval", "ease of doing business",
            "sez", "fast track", "self-certification", "self certification",
            "labour law", "labor law",
            # Spanish
            "ventanilla única", "aprobación", "licencia", "cumplimiento",
            "registro", "trámite", "facilitación", "permiso",
            "marco regulatorio", "simplificación",
        ],
        "Innovation / R&D / Patent": [
            # English
            "patent", "r&d", "research and development", "innovation lab",
            "innovation", "prototype", "prototyping", "intellectual property",
            "quality certification", "accelerator", "incubator", "centre of excellence",
            "center of excellence", "coe", "ip box",
            # Spanish
            "innovación", "investigación y desarrollo", "i+d",
            "patente", "propiedad intelectual", "prototipo",
            "centro de excelencia", "incubadora",
        ],
        "Others": [
            # English
            "green", "sustainability", "women employee", "female employee",
            "csr", "customised package", "customized package",
            "mega project", "special package", "esg",
            # Spanish
            "sostenibilidad", "verde", "mujer trabajadora", "género",
            "responsabilidad social", "paquete especial", "régimen especial",
        ],
    }

    SCOPE_MARKERS = {
        "Specific to Tier 1 cities": [
            "tier 1", "tier-1", "tier i", "zone i ", "zone-i", "zone 1",
            "bengaluru", "bangalore", "mumbai", "pune", "chennai",
            "hyderabad", "ahmedabad", "vadodara", "indore", "bhopal",
            "lucknow", "noida", "ghaziabad", "gautambuddha nagar",
            "jaipur",
        ],
        "Specific to Tier 2 & 3 cities": [
            "tier 2", "tier-2", "tier ii", "tier 3", "tier-3", "tier iii",
            "zone ii", "zone-ii", "zone 2",
            "beyond bengaluru", "beyond bangalore", "hosur", "coimbatore",
            "mysuru", "mysore", "mangaluru", "gwalior", "jabalpur",
            "kanpur", "varanasi", "agra", "prayagraj", "udaipur",
            "kota", "jodhpur",
        ],
    }

    SKIP_PATTERNS = [
        # English boilerplate
        re.compile(r"^(to position|to establish|to attract|to promote|to foster|to enhance|to sustain|to align|to drive|to facilitate)", re.I),
        re.compile(r"^(establish|promote|foster|enhance|sustain|align|attract|facilitate|generate)\b", re.I),
        re.compile(r"\b(means|shall mean)\b", re.I),
        re.compile(r"^[A-Za-z]+\s+(means|shall mean)", re.I),
        re.compile(r"\b(committee|chairman|member secretary|sachivalaya|gandhinagar|notification|gazette|finance department|secretariat)\b", re.I),
        re.compile(r"\b(name a few|to name)\b", re.I),
        re.compile(r"\b(vision|mission|aim|objective|preamble)\b.{0,80}$", re.I),
        # Spanish boilerplate
        re.compile(r"\b(considerando|por tanto|decreta|publíquese|gaceta oficial)\b", re.I),
        re.compile(r"^(art[ií]culo|cap[ií]tulo|secci[oó]n)\s+\d", re.I),
        re.compile(r"\b(definici[oó]n|se entiende por|para los efectos)\b", re.I),
    ]

    MIN_PARAGRAPH_LEN = 50

    @classmethod
    def bucket(cls, paragraphs):

        buckets = {
            it: {scope: [] for scope in cls.SCOPES}
            for it in cls.INCENTIVE_TYPES
        }

        for para in paragraphs:

            text = para["text"]

            if len(text) < cls.MIN_PARAGRAPH_LEN:
                continue

            if cls._is_skip(text, para.get("heading", "")):
                continue

            incentive_type = cls._classify_type(text)

            if not incentive_type:
                continue

            scope = cls._classify_scope(text)

            buckets[incentive_type][scope].append(text)

        return buckets

    @classmethod
    def _is_skip(cls, text, heading):

        head_low = heading.lower()

        if any(
            kw in head_low
            for kw in ("preamble", "vision", "mission", "objectives",
                       "aims", "definitions", "definition", "interpretation",
                       "budgetary", "power to amend",
                       "policy implementation")
        ):
            return True

        for pat in cls.SKIP_PATTERNS:

            if pat.search(text[:120]):
                return True

        return False

    @classmethod
    def _classify_type(cls, text):

        text_low = text.lower()

        best_type = None

        best_score = 0

        for incentive_type, keywords in cls.KEYWORD_MAP.items():

            score = sum(
                len(re.findall(rf"\b{re.escape(kw)}\b", text_low))
                for kw in keywords
            )

            if score > best_score:

                best_score = score
                best_type = incentive_type

        return best_type

    @classmethod
    def _classify_scope(cls, text):

        text_low = text.lower()

        for scope, markers in cls.SCOPE_MARKERS.items():

            if any(marker in text_low for marker in markers):

                return scope

        return "Across the state (Common)"
