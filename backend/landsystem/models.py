from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import os


# All 31 of Tanzania's regions (26 mainland + 5 Zanzibar). Shared by
# OfficerProfile and Case so region codes stay in sync everywhere.
TANZANIA_REGIONS = [
    ('arusha', 'Arusha'),
    ('dar_es_salaam', 'Dar es Salaam'),
    ('dodoma', 'Dodoma'),
    ('geita', 'Geita'),
    ('iringa', 'Iringa'),
    ('kagera', 'Kagera'),
    ('katavi', 'Katavi'),
    ('kigoma', 'Kigoma'),
    ('kilimanjaro', 'Kilimanjaro'),
    ('lindi', 'Lindi'),
    ('manyara', 'Manyara'),
    ('mara', 'Mara'),
    ('mbeya', 'Mbeya'),
    ('morogoro', 'Morogoro'),
    ('mtwara', 'Mtwara'),
    ('mwanza', 'Mwanza'),
    ('njombe', 'Njombe'),
    ('pwani', 'Pwani (Coast)'),
    ('rukwa', 'Rukwa'),
    ('ruvuma', 'Ruvuma'),
    ('shinyanga', 'Shinyanga'),
    ('simiyu', 'Simiyu'),
    ('singida', 'Singida'),
    ('songwe', 'Songwe'),
    ('tabora', 'Tabora'),
    ('tanga', 'Tanga'),
    ('kaskazini_unguja', 'Kaskazini Unguja (North Unguja)'),
    ('kusini_unguja', 'Kusini Unguja (South Unguja)'),
    ('mjini_magharibi', 'Mjini Magharibi (Urban West)'),
    ('kaskazini_pemba', 'Kaskazini Pemba (North Pemba)'),
    ('kusini_pemba', 'Kusini Pemba (South Pemba)'),
]

# Districts/councils within each region, for the district dropdown shown
# when registering a Village/Street/Ward officer. Best-effort from publicly
# documented administrative divisions - Tanzania has periodically split
# districts into more councils, so this may not reflect the very latest
# subdivisions. Correct/extend here if a district is missing.
DISTRICTS_BY_REGION = {
    'arusha': ['Arusha City', 'Arusha', 'Karatu', 'Longido', 'Meru', 'Monduli', 'Ngorongoro'],
    'dar_es_salaam': ['Ilala', 'Kinondoni', 'Temeke', 'Ubungo', 'Kigamboni'],
    'dodoma': ['Dodoma City', 'Bahi', 'Chamwino', 'Chemba', 'Kondoa', 'Kondoa Town', 'Mpwapwa', 'Kongwa'],
    'geita': ['Geita Town', 'Geita', 'Bukombe', 'Chato', 'Mbogwe', "Nyang'hwale"],
    'iringa': ['Iringa Municipal', 'Iringa', 'Kilolo', 'Mafinga Town', 'Mufindi'],
    'kagera': ['Bukoba Municipal', 'Bukoba', 'Biharamulo', 'Karagwe', 'Kyerwa', 'Missenyi', 'Muleba', 'Ngara'],
    'katavi': ['Mpanda Town', 'Mpanda', 'Mlele', 'Nsimbo'],
    'kigoma': ['Kigoma-Ujiji', 'Kasulu Town', 'Kasulu', 'Kibondo', 'Buhigwe', 'Kakonko', 'Uvinza'],
    'kilimanjaro': ['Moshi Municipal', 'Moshi', 'Hai', 'Mwanga', 'Rombo', 'Same', 'Siha'],
    'lindi': ['Lindi Municipal', 'Lindi', 'Kilwa', 'Liwale', 'Nachingwea', 'Ruangwa'],
    'manyara': ['Babati Town', 'Babati', 'Hanang', 'Kiteto', 'Mbulu', 'Simanjiro'],
    'mara': ['Musoma Municipal', 'Musoma', 'Bunda', 'Butiama', 'Rorya', 'Serengeti', 'Tarime'],
    'mbeya': ['Mbeya City', 'Mbeya', 'Busokelo', 'Chunya', 'Kyela', 'Rungwe'],
    'morogoro': ['Morogoro Municipal', 'Morogoro', 'Gairo', 'Kilombero', 'Kilosa', 'Malinyi', 'Mvomero', 'Ulanga'],
    'mtwara': ['Mtwara Municipal', 'Mtwara', 'Masasi Town', 'Masasi', 'Nanyumbu', 'Newala', 'Tandahimba'],
    'mwanza': ['Ilemela', 'Nyamagana', 'Kwimba', 'Magu', 'Misungwi', 'Sengerema', 'Ukerewe'],
    'njombe': ['Njombe Town', 'Njombe', 'Ludewa', 'Makambako', 'Makete', "Wanging'ombe"],
    'pwani': ['Kibaha Town', 'Kibaha', 'Bagamoyo', 'Kisarawe', 'Mafia', 'Mkuranga', 'Rufiji'],
    'rukwa': ['Sumbawanga Municipal', 'Sumbawanga', 'Kalambo', 'Nkasi'],
    'ruvuma': ['Songea Municipal', 'Songea', 'Mbinga', 'Namtumbo', 'Nyasa', 'Tunduru'],
    'shinyanga': ['Shinyanga Municipal', 'Shinyanga', 'Kahama Town', 'Kishapu', 'Msalala', 'Ushetu'],
    'simiyu': ['Bariadi Town', 'Bariadi', 'Busega', 'Itilima', 'Maswa', 'Meatu'],
    'singida': ['Singida Municipal', 'Singida', 'Ikungi', 'Iramba', 'Manyoni', 'Mkalama'],
    'songwe': ['Vwawa', 'Ileje', 'Mbozi', 'Momba', 'Songwe'],
    'tabora': ['Tabora Municipal', 'Igunga', 'Kaliua', 'Nzega', 'Sikonge', 'Urambo', 'Uyui'],
    'tanga': ['Tanga City', 'Handeni Town', 'Handeni', 'Kilindi', 'Korogwe Town', 'Korogwe', 'Lushoto', 'Mkinga', 'Muheza', 'Pangani'],
    'kaskazini_unguja': ['Kaskazini A', 'Kaskazini B'],
    'kusini_unguja': ['Kati', 'Kusini'],
    'mjini_magharibi': ['Mjini', 'Magharibi A', 'Magharibi B'],
    'kaskazini_pemba': ['Wete', 'Micheweni'],
    'kusini_pemba': ['Chake Chake', 'Mkoani'],
}

# Wards within each district, for the ward dropdown shown when registering a
# Village/Street/Ward officer (chosen after district). This is NOT
# exhaustive - Tanzania has several thousand wards nationwide and many are
# not reliably documented publicly, so only districts with well-verified
# ward lists are included here. For any district not listed, the
# registration form falls back to a free-text ward field instead of a
# dropdown, so registration always works - add a district's ward list here
# once you have an authoritative source (e.g. TAMISEMI/NBS) to switch it
# over to a dropdown.
WARDS_BY_DISTRICT = {
    'Ilala': [
        'Buguruni', 'Chanika', 'Gongo la Mboto', 'Ilala', 'Jangwani',
        'Kariakoo', 'Kipawa', 'Kisutu', 'Kiwalani', 'Mchikichini',
        'Msongola', 'Pugu', 'Segerea', 'Tabata', 'Ukonga',
        'Upanga Magharibi', 'Upanga Mashariki', 'Vingunguti', 'Kivukoni',
    ],
    'Kinondoni': [
        'Bunju', 'Hananasif', 'Kawe', 'Kigogo', 'Kijitonyama', 'Kinondoni',
        'Kunduchi', 'Mabwepande', 'Magomeni', 'Makongo', 'Makumbusho',
        'Mbezi Juu', 'Mbweni', 'Mikocheni', 'Msasani', 'Mwananyamala',
        'Mzimuni', 'Ndugumbi', 'Tandale', 'Wazo',
    ],
    'Temeke': [
        'Azimio', 'Chang\'ombe', 'Kigamboni', 'Kurasini', 'Mbagala',
        'Miburani', 'Sandali', 'Tandika', 'Temeke', 'Yombo Vituka',
        'Keko', 'Mtoni',
    ],
    'Arusha City': [
        'Baraa', 'Elerai', 'Engutoto', 'Kaloleni', 'Kimandolu', 'Kati',
        'Lemara', 'Levolosi', 'Muriet', 'Ngarenaro', 'Olasiti', 'Sekei',
        'Sombetini', 'Terrat', 'Themi', 'Unga Limited',
    ],
    'Dodoma City': [
        'Chamwino', 'Chidachi', 'Hombolo', 'Kikuyu', 'Kizota', 'Makole',
        'Mkonze', 'Mnadani', 'Nkuhungu', 'Ntyuka', 'Uhuru', 'Viwandani',
        'Zuzu',
    ],
    'Mbeya City': [
        'Forest', 'Iyunga', 'Ilomba', 'Isanga', 'Itagano', 'Itezi',
        'Iyela', 'Ruanda', 'Sisimba', 'Sokoine', 'Uyole',
    ],
    'Moshi Municipal': [
        'Bondeni', 'Kaloleni', 'Kiusa', 'Longuo', 'Majengo', 'Mawenzi',
        'Msaranga', 'Njoro', 'Pasua', 'Rau', 'Shantytown', 'Soweto',
    ],
    'Morogoro Municipal': [
        'Boma', 'Kihonda', 'Kingo', 'Kingolwira', 'Mafiga', 'Mazimbu',
        'Mbuyuni', 'Mji Mkuu', 'Mwembesongo', 'Sabasaba', 'Sultan Area',
    ],
    'Ilemela': ['Buswelu', 'Bugogwa', 'Igoma', 'Kirumba', 'Mkolani', 'Nyamanoro'],
    'Nyamagana': ['Butimba', 'Igogo', 'Isamilo', 'Mahina', 'Mirongo', 'Mkuyuni', 'Nyamagana', 'Pamba'],
    'Tanga City': ['Chumbageni', 'Makorora', 'Mzingani', 'Ngamiani Kaskazini', 'Ngamiani Kusini', 'Tanga'],
    'Songea Municipal': ['Bombambili', 'Mji Mkuu', 'Mshangano', 'Msamala', 'Ruvuma'],
}

# Streets/mitaa (for Street officers) and villages/vitongoji (for Village
# officers) within each ward, for the dropdown shown after picking a ward
# during registration. Starts empty deliberately - this level of detail
# isn't reliably documented publicly, so rather than guess, the
# registration form falls back to a free-text field for every ward until an
# authoritative list is added here, keyed by ward name (e.g.
# STREETS_BY_WARD['Kariakoo'] = ['Congo', 'Livingstone', ...]).
STREETS_BY_WARD = {
    'Makongo': ['Changanyikeni', 'Makongo Juu', 'Mlalakuwa', 'Mbuyuni'],
}


class Citizen(models.Model):
    """Model for citizen users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='citizen_profile')
    phone = models.CharField(max_length=20)
    region = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'citizens'
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"


class OfficerProfile(models.Model):
    """Model for case officer profiles"""
    REGION_CHOICES = TANZANIA_REGIONS

    # Ordered lowest to highest. A case starts at the first level and
    # escalation moves it one step down this list at a time.
    LEVEL_CHOICES = [
        ('village', 'Village Officer'),
        ('street', 'Street Officer'),
        ('ward', 'Ward Officer'),
        ('district_land_officer', 'District Land Officer'),
        ('regional', 'Regional Officer'),
        ('high_court', 'High Court'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='officer_profile')
    region = models.CharField(max_length=50, choices=REGION_CHOICES)
    level = models.CharField(max_length=30, choices=LEVEL_CHOICES, default='village')
    # Which district (within region) a Village/Street/Ward officer's
    # jurisdiction falls under - chosen from DISTRICTS_BY_REGION. Not used
    # for District Land Officers, whose `jurisdiction` field already names
    # their district directly, or Regional/High Court, who cover the whole
    # region.
    district = models.CharField(max_length=100, blank=True)
    # The specific ward a Village/Street/Ward officer's area falls under -
    # chosen from WARDS_BY_DISTRICT where available, otherwise typed in
    # directly. For a Ward officer, this IS their jurisdiction (mirrored into
    # `jurisdiction` below); for Village/Street officers it's the ward their
    # village/street sits in, one level more specific than `district`.
    ward = models.CharField(max_length=255, blank=True)
    # The specific village/street/ward/district name this officer serves
    # within their region - e.g. "Chamwino" for a village officer, "Makole"
    # for a ward officer. Not applicable for Regional/High Court officers,
    # who cover the whole region.
    jurisdiction = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'officers'

    def __str__(self):
        place = f"{self.jurisdiction}, {self.get_region_display()}" if self.jurisdiction else self.get_region_display()
        return f"{self.get_level_display()} - {self.user.username} ({place})"


class Case(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('escalated', 'Escalated'),
    ]
    
    # Same region list as OfficerProfile.REGION_CHOICES.
    REGION_CHOICES = OfficerProfile.REGION_CHOICES

    # Same ordered hierarchy as OfficerProfile.LEVEL_CHOICES. A case starts
    # with the village officer and escalation steps it up one level at a time.
    LEVEL_CHOICES = OfficerProfile.LEVEL_CHOICES

    title = models.CharField(max_length=255)
    citizen = models.ForeignKey(Citizen, on_delete=models.CASCADE, null=True, blank=True, related_name='submitted_cases')
    citizen_name = models.CharField(max_length=255)
    citizen_phone = models.CharField(max_length=20)
    citizen_email = models.EmailField(blank=True)
    description = models.TextField()
    location = models.CharField(max_length=255)
    # The citizen's own village/ward, as they name it - not validated against
    # OfficerProfile.jurisdiction, which is free text set independently by officers.
    ward = models.CharField(max_length=255, blank=True, default='')
    region = models.CharField(max_length=50, choices=REGION_CHOICES, default='dodoma')
    latitude = models.FloatField()
    longitude = models.FloatField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    current_level = models.CharField(max_length=30, choices=LEVEL_CHOICES, default='village')
    # When the case arrived at current_level - NOT auto_now, since it should
    # only change when the level actually advances, not on every save. Used to
    # measure the 5-day auto-escalation window for the current level only.
    level_updated_at = models.DateTimeField(default=timezone.now)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_cases')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'cases'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.status}"


class CaseFeedback(models.Model):
    """A citizen's review of how their case was handled. One per case -
    resubmitting updates the existing review rather than creating a new one."""
    RATING_CHOICES = [
        ('solved', 'Solved'),
        ('not_solved', 'Not Solved'),
        ('not_listened', 'Not Listened To'),
    ]

    case = models.OneToOneField(Case, on_delete=models.CASCADE, related_name='feedback')
    rating = models.CharField(max_length=20, choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'case_feedback'

    def __str__(self):
        return f"{self.get_rating_display()} - Case #{self.case_id}"


class CaseDocument(models.Model):
    """Model for case evidence documents"""
    DOCUMENT_TYPES = [
        ('evidence', 'Evidence'),
        ('receipt', 'Receipt'),
        ('photo', 'Photo'),
        ('letter', 'Letter'),
        ('contract', 'Contract'),
        ('other', 'Other'),
    ]
    
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, default='evidence')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='case_documents/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_documents')
    
    class Meta:
        db_table = 'case_documents'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.title} - Case #{self.case.id}"
    
    @property
    def file_size_mb(self):
        """Return file size in MB"""
        if self.file:
            return round(self.file.size / (1024 * 1024), 2)
        return 0
    
    @property
    def file_extension(self):
        """Get file extension"""
        if self.file:
            name, ext = os.path.splitext(self.file.name)
            return ext.lstrip('.')
        return ''



