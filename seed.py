"""
seed.py — Populate bfk.db with realistic dummy data matching the admin UI.

Run from the project root:
    python seed.py

Safe to re-run — drops and recreates all tables first.
"""

import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from app.database import engine, SessionLocal, Base
from app import models


def reset_db():
    print("⚡  Dropping and recreating all tables…")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✓   Tables created")


def seed(db):

    # ─────────────────────────────────────────────
    # WEIGHT CLASSES  (BFK Amateur + KPBC Pro)
    # ─────────────────────────────────────────────
    print("🥊  Seeding weight classes…")

    ama_male = [
        ("Light Flyweight",  None,  48.0),
        ("Flyweight",        48.0,  51.0),
        ("Bantamweight",     51.0,  54.0),
        ("Featherweight",    54.0,  57.0),
        ("Lightweight",      57.0,  60.0),
        ("Light Welterweight",60.0, 63.5),
        ("Welterweight",     63.5,  67.0),
        ("Light Middleweight",67.0, 71.0),
        ("Middleweight",     71.0,  75.0),
        ("Light Heavyweight",75.0,  80.0),
        ("Super Heavyweight",80.0,  86.0),
        ("Cruiserweight",    86.0,  92.0),
        ("Heavyweight",      92.0,  999.0),
    ]
    ama_female = [
        ("Minimumweight",    None,  48.0),
        ("Light Flyweight",  48.0,  50.0),
        ("Flyweight",        50.0,  52.0),
        ("Bantamweight",     52.0,  54.0),
        ("Featherweight",    54.0,  57.0),
        ("Lightweight",      57.0,  60.0),
        ("Welterweight",     60.0,  63.0),
        ("Light Middleweight",63.0, 66.0),
        ("Middleweight",     66.0,  70.0),
        ("Light Heavyweight",70.0,  75.0),
        ("Super Heavyweight",75.0,  81.0),
        ("Heavyweight",      81.0,  999.0),
    ]
    pro_classes = [
        ("Minimumweight",    None,  47.6),
        ("Light Flyweight",  47.6,  48.9),
        ("Flyweight",        48.9,  50.8),
        ("Super Flyweight",  50.8,  52.2),
        ("Bantamweight",     52.2,  53.5),
        ("Super Bantamweight",53.5, 55.3),
        ("Featherweight",    55.3,  57.2),
        ("Super Featherweight",57.2,58.9),
        ("Lightweight",      58.9,  61.2),
        ("Super Lightweight",61.2,  63.5),
        ("Welterweight",     63.5,  66.7),
        ("Super Welterweight",66.7, 69.9),
        ("Middleweight",     69.9,  72.6),
        ("Super Middleweight",72.6, 76.2),
        ("Light Heavyweight",76.2,  79.4),
        ("Cruiserweight",    79.4,  90.7),
        ("Heavyweight",      90.7,  999.0),
    ]

    wc_objects = {}

    for name, mn, mx in ama_male:
        wc = models.WeightClass(
            name=name, min_kg=mn, max_kg=mx,
            gender=models.GenderEnum.male,
            category=models.WeightClassCategoryEnum.amateur_male,
            governing_body=models.GoverningBodyEnum.bfk,
        )
        db.add(wc)
        db.flush()
        wc_objects[f"am_{name}"] = wc

    for name, mn, mx in ama_female:
        wc = models.WeightClass(
            name=name, min_kg=mn, max_kg=mx,
            gender=models.GenderEnum.female,
            category=models.WeightClassCategoryEnum.amateur_female,
            governing_body=models.GoverningBodyEnum.bfk,
        )
        db.add(wc)
        db.flush()
        wc_objects[f"af_{name}"] = wc

    for name, mn, mx in pro_classes:
        wc = models.WeightClass(
            name=name, min_kg=mn, max_kg=mx,
            gender=models.GenderEnum.male,
            category=models.WeightClassCategoryEnum.professional,
            governing_body=models.GoverningBodyEnum.kpbc,
        )
        db.add(wc)
        db.flush()
        wc_objects[f"pro_{name}"] = wc

    # Shorthand refs used below
    wc_lw_m   = wc_objects["am_Lightweight"]       # 60 kg men amateur
    wc_fly_m  = wc_objects["am_Flyweight"]          # 51 kg men amateur
    wc_fth_m  = wc_objects["am_Featherweight"]      # 57 kg men amateur
    wc_ww_m   = wc_objects["am_Welterweight"]       # 67 kg men amateur
    wc_mw_m   = wc_objects["am_Middleweight"]       # 75 kg men amateur
    wc_fly_f  = wc_objects["af_Flyweight"]          # 52 kg women amateur
    wc_lw_f   = wc_objects["af_Lightweight"]        # 60 kg women amateur
    wc_fth_pro = wc_objects["pro_Featherweight"]    # 57 kg pro
    wc_ww_pro  = wc_objects["pro_Welterweight"]     # 66.7 kg pro
    wc_lw_pro  = wc_objects["pro_Lightweight"]      # 61.2 kg pro

    # ─────────────────────────────────────────────
    # CLUBS
    # ─────────────────────────────────────────────
    print("🏟   Seeding clubs…")

    def make_club(name, county, town, coach_name, affil, ctype, founded,
                  phone, email, address, insurance, audit, facilities):
        c = models.Club(
            name=name, county=county, town=town, head_coach=coach_name,
            bfk_affiliation_no=affil, type=ctype,
            contact_phone=phone, contact_email=email, address=address,
            insurance_expiry=insurance, last_audit_date=audit,
            facilities=facilities, status="active",
        )
        db.add(c)
        db.flush()
        return c

    club_nrb_fist = make_club(
        "Nairobi Fist Boxing Club", "Nairobi", "Westlands", "Moses Kamau",
        "BFK-C-001", models.ClubTypeEnum.mixed,
        "2008", "+254 720 111 222", "info@nairobifist.co.ke",
        "Westlands Sports Complex, Nairobi",
        date(2025, 12, 31), date(2025, 3, 15),
        "Full gym, ring, weights room, sparring bay, video analysis suite",
    )
    club_kisumu = make_club(
        "Kisumu Amateur Boxing Club", "Kisumu", "Kisumu Central", "John Otieno",
        "BFK-C-007", models.ClubTypeEnum.amateur,
        "2014", "+254 731 222 333", "kisumu.abc@gmail.com",
        "Tom Mboya Sports Ground, Kisumu",
        date(2025, 11, 30), date(2025, 1, 20),
        "Ring, basic gym, open-air sparring area",
    )
    club_mombasa = make_club(
        "Mombasa Amateur Boxing Club", "Mombasa", "Mombasa Island", "Ali Hassan",
        "BFK-C-003", models.ClubTypeEnum.amateur,
        "2011", "+254 742 333 444", "mombasa.abc@mail.com",
        "Mombasa Sports Club, Mombasa",
        date(2025, 10, 31), date(2025, 4, 10),
        "Full indoor gym, competition ring",
    )
    club_rift = make_club(
        "Rift Valley Boxing Club", "Uasin Gishu", "Eldoret", "Simon Korir",
        "BFK-C-011", models.ClubTypeEnum.mixed,
        "2010", "+254 753 444 555", "riftvalleybc@mail.com",
        "Eldoret Sports Ground, Eldoret",
        date(2026, 1, 31), date(2025, 2, 28),
        "Full gym, competition ring, video analysis suite, women's section",
    )
    club_kiambu = make_club(
        "Kiambu Strikers Boxing Club", "Kiambu", "Thika", "Paul Gathitu",
        "BFK-C-015", models.ClubTypeEnum.amateur,
        "2017", "+254 764 555 666", "kiambu.strikers@mail.com",
        "Thika Greens Sports Hall, Thika",
        date(2025, 9, 30), date(2025, 6, 1),
        "Basic gym, half-size ring",
    )
    club_nakuru = make_club(
        "Nakuru Boxing Club", "Nakuru", "Nakuru Town", "Peter Odhiambo",
        "BFK-C-009", models.ClubTypeEnum.amateur,
        "2012", "+254 775 666 777", "nakuru.bc@mail.com",
        "Afraha Stadium Annex, Nakuru",
        date(2025, 8, 31), date(2025, 5, 20),
        "Gym, ring, basic sparring area",
    )

    # ─────────────────────────────────────────────
    # COACHES
    # ─────────────────────────────────────────────
    print("👨‍🏫  Seeding coaches…")

    def make_coach(first, last, licence, phone, county, dob, club_id, certs, years):
        c = models.Coach(
            first_name=first, last_name=last, licence_number=licence,
            phone=phone, county=county, date_of_birth=dob,
            club_id=club_id, certifications=certs,
            years_coaching=years, status="active",
        )
        db.add(c)
        db.flush()
        return c

    coach_kamau  = make_coach("Moses",  "Kamau",   "BFK-COACH-001", "+254 720 100 200",
                               "Nairobi",  date(1975, 3, 15), club_nrb_fist.id,
                               "IBA L3,KPBC Licensed,First Aid & CPR,Strength & Conditioning", 18)
    coach_otieno = make_coach("John",   "Otieno",  "BFK-COACH-007", "+254 731 200 300",
                               "Kisumu",   date(1981, 8, 22), club_kisumu.id,
                               "IBA L2,First Aid", 11)
    coach_hassan = make_coach("Ali",    "Hassan",  "BFK-COACH-003", "+254 742 300 400",
                               "Mombasa",  date(1979, 12, 8), club_mombasa.id,
                               "IBA L2,First Aid & CPR", 13)
    coach_korir  = make_coach("Simon",  "Korir",   "BFK-COACH-011", "+254 753 400 500",
                               "Uasin Gishu", date(1977, 5, 1), club_rift.id,
                               "IBA L3,AIBA Certified,First Aid", 16)
    coach_gathitu = make_coach("Paul", "Gathitu",  "BFK-COACH-015", "+254 764 500 600",
                                "Kiambu",  date(1983, 6, 30), club_kiambu.id,
                                "IBA L1", 7)
    coach_odhiambo = make_coach("Peter","Odhiambo","BFK-COACH-009", "+254 775 600 700",
                                 "Nakuru",  date(1980, 9, 14), club_nakuru.id,
                                 "IBA L2,First Aid", 10)

    # ─────────────────────────────────────────────
    # FIGHTERS
    # ─────────────────────────────────────────────
    print("🥊  Seeding fighters…")

    def make_fighter(licence, first, last, nick, dob, gender, county, town,
                     phone, email, id_no, blood, status=models.FighterStatusEnum.active):
        f = models.Fighter(
            licence_number=licence, first_name=first, last_name=last,
            nickname=nick, date_of_birth=dob, gender=gender,
            county=county, town=town, phone=phone, email=email,
            id_number=id_no, blood_type=blood, nationality="Kenyan",
            status=status,
        )
        db.add(f)
        db.flush()
        return f

    f_omondi   = make_fighter("BFK-M-2021-012","Evans",  "Omondi",   "The Kisumu Kid",
                               date(1998,3,4),  models.GenderEnum.male,   "Kisumu","Kisumu Central",
                               "+254 712 345 678","e.omondi@mail.com","29384756","O+")

    f_chepkemoi= make_fighter("BFK-F-2024-089","Joyce",  "Chepkemoi","Iron Rose",
                               date(2001,9,18), models.GenderEnum.female, "Eldoret","Eldoret North",
                               "+254 722 987 654","j.chepkemoi@mail.com","38472910","A+")

    f_mwangi   = make_fighter("BFK-M-2019-004","Peter",  "Mwangi",   "Nganga",
                               date(1993,7,12), models.GenderEnum.male,   "Nairobi","Embakasi",
                               "+254 733 456 789","p.mwangi@mail.com","21938475","B+")

    f_njoroge  = make_fighter("BFK-M-2022-031","David",  "Njoroge",  "The Wall",
                               date(1999,11,29),models.GenderEnum.male,   "Kiambu","Thika",
                               "+254 744 321 654","d.njoroge@mail.com","34829102","O-",
                               models.FighterStatusEnum.suspended)

    f_katana   = make_fighter("BFK-M-2024-051","Timothy","Katana",   "Coast Hawk",
                               date(2004,2,3),  models.GenderEnum.male,   "Mombasa","Nyali",
                               "+254 755 654 321","t.katana@mail.com","44729103","A-")

    f_wanjiku  = make_fighter("BFK-M-2020-007","Samuel", "Wanjiku",  "Baba Yao",
                               date(1995,5,20), models.GenderEnum.male,   "Nairobi","Dagoretti",
                               "+254 721 876 543","s.wanjiku@mail.com","25038471","B-")

    f_njeri    = make_fighter("BFK-F-2023-066","Grace",  "Njeri",    "Mama Boxer",
                               date(1997,6,11), models.GenderEnum.female, "Nakuru","Nakuru Town",
                               "+254 766 543 210","g.njeri@mail.com","32847201","AB+")

    f_mutua    = make_fighter("BFK-M-2018-022","Felix",  "Mutua",    "The Shark",
                               date(1991,4,17), models.GenderEnum.male,   "Mombasa","Kisauni",
                               "+254 777 432 100","f.mutua@mail.com","18274635","A+",
                               models.FighterStatusEnum.suspended)

    f_ochieng  = make_fighter("BFK-M-2023-038","Brian",  "Ochieng",  "B-Train",
                               date(2000,1,8),  models.GenderEnum.male,   "Kisumu","Kisumu West",
                               "+254 788 321 000","b.ochieng@mail.com","40192837","O+",
                               models.FighterStatusEnum.suspended)

    f_waweru   = make_fighter("BFK-M-2021-019","Mark",   "Waweru",   "The Ghost",
                               date(1997,8,25), models.GenderEnum.male,   "Nairobi","Karen",
                               "+254 799 210 111","m.waweru@mail.com","35746290","B+")

    f_achieng  = make_fighter("BFK-F-2022-055","Mary",   "Achieng",  "Sweet Mary",
                               date(2000,3,15), models.GenderEnum.female, "Nairobi","Eastlands",
                               "+254 710 111 222","m.achieng@mail.com","37291847","A-")

    f_mutiso   = make_fighter("BFK-M-2021-028","Collins","Mutiso",   "The Machakos Bull",
                               date(1999,7,22), models.GenderEnum.male,   "Machakos","Machakos Town",
                               "+254 721 222 333","c.mutiso@mail.com","38192746","O+")

    all_fighters = [
        f_omondi,f_chepkemoi,f_mwangi,f_njoroge,f_katana,
        f_wanjiku,f_njeri,f_mutua,f_ochieng,f_waweru,f_achieng,f_mutiso
    ]

    # ─────────────────────────────────────────────
    # CLUB HISTORY
    # ─────────────────────────────────────────────
    club_map = [
        (f_omondi,    club_kisumu,    date(2021,1,10)),
        (f_chepkemoi, club_rift,      date(2022,3,1)),
        (f_mwangi,    club_nrb_fist,  date(2019,6,15)),
        (f_njoroge,   club_kiambu,    date(2022,4,1)),
        (f_katana,    club_mombasa,   date(2024,1,20)),
        (f_wanjiku,   club_nrb_fist,  date(2020,2,5)),
        (f_njeri,     club_nakuru,    date(2023,3,1)),
        (f_mutua,     club_mombasa,   date(2018,7,1)),
        (f_ochieng,   club_kisumu,    date(2023,1,15)),
        (f_waweru,    club_nrb_fist,  date(2021,3,10)),
        (f_achieng,   club_nrb_fist,  date(2022,6,1)),
        (f_mutiso,    club_nrb_fist,  date(2021,9,1)),
    ]
    for fighter, club, joined in club_map:
        db.add(models.FighterClubHistory(
            fighter_id=fighter.id, club_id=club.id,
            joined_date=joined, is_current=True,
        ))

    # ─────────────────────────────────────────────
    # COACH ASSIGNMENTS
    # ─────────────────────────────────────────────
    coach_map = [
        (f_omondi,    coach_otieno,  True),
        (f_chepkemoi, coach_korir,   True),
        (f_mwangi,    coach_kamau,   True),
        (f_njoroge,   coach_gathitu, True),
        (f_katana,    coach_hassan,  True),
        (f_wanjiku,   coach_kamau,   True),
        (f_njeri,     coach_odhiambo,True),
        (f_mutua,     coach_hassan,  True),
        (f_ochieng,   coach_otieno,  True),
        (f_waweru,    coach_kamau,   True),
        (f_achieng,   coach_kamau,   True),
        (f_mutiso,    coach_kamau,   True),
    ]
    for fighter, coach, primary in coach_map:
        db.add(models.FighterCoach(
            fighter_id=fighter.id, coach_id=coach.id,
            is_primary=primary, role="Head Trainer",
            assigned_date=date(2021,1,1), is_active=True,
        ))

    # ─────────────────────────────────────────────
    # PHYSICAL PROFILES
    # ─────────────────────────────────────────────
    physicals = [
        (f_omondi,    60.2, 174, 178, models.StanceEnum.orthodox,  date(2025,1,4)),
        (f_chepkemoi, 50.9, 162, 165, models.StanceEnum.orthodox,  date(2024,12,12)),
        (f_mwangi,    66.8, 178, 182, models.StanceEnum.southpaw,  date(2025,6,22)),
        (f_njoroge,   74.5, 180, 183, models.StanceEnum.orthodox,  date(2025,7,11)),
        (f_katana,    50.8, 165, 167, models.StanceEnum.orthodox,  date(2025,6,20)),
        (f_wanjiku,   57.1, 170, 174, models.StanceEnum.orthodox,  date(2025,3,10)),
        (f_njeri,     59.5, 168, 170, models.StanceEnum.southpaw,  date(2024,8,15)),
        (f_mutua,     56.9, 169, 172, models.StanceEnum.orthodox,  date(2025,3,1)),
        (f_waweru,    67.4, 176, 180, models.StanceEnum.orthodox,  date(2025,4,1)),
        (f_achieng,   51.5, 163, 166, models.StanceEnum.orthodox,  date(2025,2,1)),
        (f_mutiso,    59.8, 173, 176, models.StanceEnum.southpaw,  date(2025,1,15)),
    ]
    for f, wt, ht, rc, stance, mdate in physicals:
        db.add(models.PhysicalProfile(
            fighter_id=f.id, weight_kg=wt, height_cm=ht,
            reach_cm=rc, stance=stance, measured_on=mdate,
            measured_by="BFK Official",
        ))

    # ─────────────────────────────────────────────
    # BOXING RECORDS
    # ─────────────────────────────────────────────
    records = [
        # fighter, W, L, D, wko, wtko, wdec, lko, ltko, ldec, nc, level, cat
        (f_omondi,    14,2,0, 8,3,3, 1,0,1, 0, models.ExperienceLevelEnum.advanced,      "professional"),
        (f_chepkemoi,  8,1,0, 2,3,3, 0,0,1, 0, models.ExperienceLevelEnum.advanced,      "amateur"),
        (f_mwangi,    22,5,1, 9,6,7, 2,1,2, 0, models.ExperienceLevelEnum.professional,  "professional"),
        (f_njoroge,    5,3,0, 1,2,2, 1,1,1, 0, models.ExperienceLevelEnum.intermediate,  "amateur"),
        (f_katana,     2,0,0, 1,0,1, 0,0,0, 0, models.ExperienceLevelEnum.novice,        "amateur"),
        (f_wanjiku,   18,3,2, 7,5,6, 1,1,1, 0, models.ExperienceLevelEnum.advanced,      "professional"),
        (f_njeri,      4,2,1, 1,1,2, 0,1,1, 0, models.ExperienceLevelEnum.intermediate,  "amateur"),
        (f_mutua,     11,8,1, 3,3,5, 3,2,3, 0, models.ExperienceLevelEnum.intermediate,  "professional"),
        (f_ochieng,    6,4,0, 2,1,3, 1,2,1, 0, models.ExperienceLevelEnum.intermediate,  "amateur"),
        (f_waweru,     8,3,0, 2,3,3, 1,1,1, 0, models.ExperienceLevelEnum.intermediate,  "amateur"),
        (f_achieng,    3,3,1, 0,1,2, 0,1,2, 0, models.ExperienceLevelEnum.intermediate,  "amateur"),
        (f_mutiso,    12,3,0, 4,4,4, 1,1,1, 0, models.ExperienceLevelEnum.advanced,      "amateur"),
    ]
    for (f, w,l,d, wko,wtko,wdec, lko,ltko,ldec, nc, lvl, cat) in records:
        db.add(models.BoxingRecord(
            fighter_id=f.id,
            total_fights=w+l+d+nc,
            wins=w, losses=l, draws=d,
            wins_by_ko=wko, wins_by_tko=wtko, wins_by_decision=wdec,
            losses_by_ko=lko, losses_by_tko=ltko, losses_by_decision=ldec,
            no_contests=nc,
            experience_level=lvl,
            category=cat,
        ))

    # ─────────────────────────────────────────────
    # MEDICAL RECORDS
    # ─────────────────────────────────────────────
    medicals = [
        (f_omondi,    date(2025,1,4),  "Dr. James Kibuchi",  True,  "120/78","Normal","20/20","Negative","Negative",date(2026,1,31),"Fit for competition. No abnormalities."),
        (f_chepkemoi, date(2024,12,12),"Dr. Sarah Ngugi",    True,  "115/72","Normal","20/20","Negative","Negative",date(2025,12,31),"Excellent health. Cleared for all competitions."),
        (f_mwangi,    date(2025,6,22), "Dr. Sarah Ngugi",    True,  "122/80","Normal","20/20","Negative","Negative",date(2026,6,30),"Healthy. Minor scar tissue above left eye — no restrictions."),
        (f_njoroge,   date(2025,7,11), "Dr. James Kibuchi",  False, "145/92","Under Review","20/20","Negative","Negative",None,"Elevated BP post-KO. Mandatory 30-day hold. Must re-examine before return."),
        (f_katana,    date(2025,6,20), "Dr. Ali Hassan",     True,  "110/68","Normal","20/20","Negative","Negative",date(2026,6,30),"Young athlete in excellent health. No concerns."),
        (f_wanjiku,   date(2025,3,10), "Dr. James Kibuchi",  True,  "118/76","Normal","20/20","Negative","Negative",date(2026,3,31),"Fit. Regular dehydration management plan in place."),
        (f_njeri,     date(2024,8,15), "Dr. Robert Otieno",  True,  "118/75","Normal","20/25","Negative","Negative",date(2025,8,31),"Mild myopia noted — no restrictions. Licence expires Aug 2025."),
        (f_mutua,     date(2025,6,28), "Dr. Peter Odhiambo", False, "130/85","Normal","20/20","Negative","Negative",None,"Post-KO suspension. CT scan recommended before return."),
        (f_waweru,    date(2025,5,5),  "Dr. James Kibuchi",  True,  "119/78","Normal","20/20","Negative","Negative",date(2026,5,31),"Cleared post-suspension. Full neurological exam completed."),
        (f_achieng,   date(2025,2,1),  "Dr. Sarah Ngugi",    True,  "112/70","Normal","20/20","Negative","Negative",date(2026,2,28),"Healthy. No restrictions."),
        (f_mutiso,    date(2025,1,15), "Dr. James Kibuchi",  True,  "121/79","Normal","20/20","Negative","Negative",date(2026,1,31),"Cleared for competition."),
    ]
    for (f, edate, doc, cleared, bp, ecg, eyes, hiv, hep, expiry, notes) in medicals:
        db.add(models.MedicalRecord(
            fighter_id=f.id,
            exam_date=edate, doctor_name=doc,
            cleared_to_compete=cleared,
            blood_pressure=bp, ecg_result=ecg, eye_test_result=eyes,
            hiv_status=hiv, hepatitis_status=hep,
            licence_expiry=expiry, notes=notes,
        ))

    # ─────────────────────────────────────────────
    # EVENTS
    # ─────────────────────────────────────────────
    print("📋  Seeding events…")

    ev_kisumu = models.Event(
        name="Kisumu County Championships 2025",
        event_date=date(2025,7,10), venue="Tom Mboya Sports Ground",
        county="Kisumu", event_type=models.EventTypeEnum.amateur,
        sanctioning_body=models.GoverningBodyEnum.bfk,
        promoter="Kisumu County Sports Office",
        head_official="Julius Makokha",
        status=models.EventStatusEnum.completed,
    )
    ev_nrb_pro = models.Event(
        name="Nairobi Pro Boxing Night",
        event_date=date(2025,6,28), venue="Carnivore Grounds",
        county="Nairobi", event_type=models.EventTypeEnum.professional,
        sanctioning_body=models.GoverningBodyEnum.kpbc,
        promoter="Nairobi Fight Nights Ltd",
        head_official="Charles Omondi",
        status=models.EventStatusEnum.completed,
    )
    ev_nrb_open = models.Event(
        name="Nairobi Open Championship 2025",
        event_date=date(2025,8,14), venue="Nyayo National Stadium",
        county="Nairobi", event_type=models.EventTypeEnum.amateur,
        sanctioning_body=models.GoverningBodyEnum.bfk,
        promoter="Kenya Sports Ltd",
        head_official="Julius Makokha",
        status=models.EventStatusEnum.upcoming,
    )
    ev_msa_cfn = models.Event(
        name="Mombasa Coastal Fight Night",
        event_date=date(2025,8,22), venue="Mombasa Sports Club",
        county="Mombasa", event_type=models.EventTypeEnum.professional,
        sanctioning_body=models.GoverningBodyEnum.kpbc,
        promoter="Coast Boxing Promotions",
        head_official="Peter Odhiambo",
        status=models.EventStatusEnum.upcoming,
    )
    ev_title_wanjiku = models.Event(
        name="BFK Featherweight Title Fight", event_date=date(2024,11,8),
        venue="KICC Grounds, Nairobi", county="Nairobi",
        event_type=models.EventTypeEnum.professional,
        sanctioning_body=models.GoverningBodyEnum.kpbc,
        promoter="ABU Eastern Africa", head_official="Charles Omondi",
        status=models.EventStatusEnum.completed,
    )
    ev_nat_champs_2024 = models.Event(
        name="BFK National Championships 2024", event_date=date(2024,3,12),
        venue="Nyayo National Stadium, Nairobi", county="Nairobi",
        event_type=models.EventTypeEnum.amateur,
        sanctioning_body=models.GoverningBodyEnum.bfk,
        promoter="BFK Secretariat", head_official="Julius Makokha",
        status=models.EventStatusEnum.completed,
    )

    for ev in [ev_kisumu, ev_nrb_pro, ev_nrb_open, ev_msa_cfn,
               ev_title_wanjiku, ev_nat_champs_2024]:
        db.add(ev)
    db.flush()

    # ─────────────────────────────────────────────
    # BOUTS
    # ─────────────────────────────────────────────
    print("🥊  Seeding bouts…")

    def make_bout(num, event, wc, fa, fb, sched_rds, btype,
                  rds_fought=None, result=None, winner=None, method=None,
                  win_rd=None, win_time=None,
                  j1n=None,j1a=None,j1b=None,
                  j2n=None,j2a=None,j2b=None,
                  j3n=None,j3a=None,j3b=None,
                  ref=None, title=None, notes=None):
        b = models.Bout(
            bout_number=num, event_id=event.id,
            weight_class_id=wc.id,
            fighter_a_id=fa.id, fighter_b_id=fb.id,
            scheduled_rounds=sched_rds, bout_type=btype,
            title_at_stake=title,
            actual_rounds_fought=rds_fought,
            result=result, winner_id=winner.id if winner else None,
            win_method=method, win_round=win_rd, win_time=win_time,
            judge1_name=j1n, judge1_score_a=j1a, judge1_score_b=j1b,
            judge2_name=j2n, judge2_score_a=j2a, judge2_score_b=j2b,
            judge3_name=j3n, judge3_score_a=j3a, judge3_score_b=j3b,
            referee=ref, notes=notes,
        )
        db.add(b)
        db.flush()
        return b

    # Kisumu Champs — 10 Jul 2025
    bout_2406 = make_bout(
        "#2406", ev_kisumu, wc_lw_m, f_omondi, f_ochieng, 3,
        models.BoutTypeEnum.non_title,
        rds_fought=4, result=models.BoutResultEnum.fighter_a,
        winner=f_omondi, method=models.WinMethodEnum.tko,
        win_rd=4, win_time="2:31", ref="Julius Makokha",
        notes="Omondi knocked down Ochieng in Rd 3. Corner threw in the towel in Rd 4.",
    )
    bout_2405 = make_bout(
        "#2405", ev_kisumu, wc_fly_f, f_chepkemoi, f_achieng, 3,
        models.BoutTypeEnum.non_title,
        rds_fought=3, result=models.BoutResultEnum.fighter_a,
        winner=f_chepkemoi, method=models.WinMethodEnum.ud,
        j1n="Judge Kamau (Nairobi)", j1a=30, j1b=27,
        j2n="Judge Oloo (Kisumu)",  j2a=30, j2b=27,
        j3n="Judge Mwangi (Mombasa)",j3a=29, j3b=28,
        ref="Ruth Wanjiku",
        notes="Chepkemoi dominated all three rounds with sharp jabs and movement.",
    )
    bout_2407 = make_bout(
        "#2407", ev_kisumu, wc_mw_m, f_njoroge, f_waweru, 3,
        models.BoutTypeEnum.non_title,
        rds_fought=5, result=models.BoutResultEnum.fighter_b,
        winner=f_waweru, method=models.WinMethodEnum.tko_medical,
        win_rd=5, win_time="1:44", ref="Julius Makokha",
        notes="Referee stopped contest after Njoroge sustained a cut above right eye. Mandatory medical suspension issued.",
    )

    # Nairobi Pro Night — 28 Jun 2025
    bout_2403 = make_bout(
        "#2403", ev_nrb_pro, wc_fth_pro, f_wanjiku, f_mutua, 10,
        models.BoutTypeEnum.non_title,
        rds_fought=2, result=models.BoutResultEnum.fighter_a,
        winner=f_wanjiku, method=models.WinMethodEnum.ko,
        win_rd=2, win_time="0:58", ref="Charles Omondi",
        notes="Wanjiku landed a devastating right hook. Mutua failed to beat the 10-count. Medical team attended immediately.",
    )
    bout_2401 = make_bout(
        "#2401", ev_nrb_pro, wc_ww_pro, f_mwangi, f_waweru, 10,
        models.BoutTypeEnum.non_title,
        rds_fought=10, result=models.BoutResultEnum.fighter_a,
        winner=f_mwangi, method=models.WinMethodEnum.sd,
        j1n="Judge Kamau (Nairobi)", j1a=97, j1b=93,
        j2n="Judge Oloo (Kisumu)",  j2a=95, j2b=95,
        j3n="Judge Mwangi (Mombasa)",j3a=94, j3b=96,
        ref="Charles Omondi",
        notes="Mwangi won a disputed split decision. Third judge scored it for Waweru.",
    )

    # National Championships 2024 — titles
    bout_title_omondi = make_bout(
        "#2201", ev_nat_champs_2024, wc_lw_m, f_omondi, f_mutiso, 3,
        models.BoutTypeEnum.title, title="Kenya National Lightweight Title",
        rds_fought=3, result=models.BoutResultEnum.fighter_a,
        winner=f_omondi, method=models.WinMethodEnum.ud,
        j1n="Judge A", j1a=30, j1b=27,
        j2n="Judge B", j2a=29, j2b=28,
        j3n="Judge C", j3a=30, j3b=27,
        ref="Julius Makokha",
        notes="Omondi wins Kenya Lightweight title in dominant fashion.",
    )
    bout_title_chepkemoi = make_bout(
        "#2202", ev_nat_champs_2024, wc_fly_f, f_chepkemoi, f_achieng, 3,
        models.BoutTypeEnum.title, title="Kenya Women Flyweight Title",
        rds_fought=3, result=models.BoutResultEnum.fighter_a,
        winner=f_chepkemoi, method=models.WinMethodEnum.ud,
        ref="Ruth Wanjiku",
        notes="Chepkemoi wins women's flyweight title.",
    )

    # ABU title — Wanjiku
    bout_abu = make_bout(
        "#2101", ev_title_wanjiku, wc_fth_pro, f_wanjiku, f_mutua, 12,
        models.BoutTypeEnum.title, title="ABU East & Central Africa Featherweight Title",
        rds_fought=12, result=models.BoutResultEnum.fighter_a,
        winner=f_wanjiku, method=models.WinMethodEnum.md,
        ref="Peter Odhiambo",
        notes="Wanjiku wins ABU East & Central Africa Featherweight title in Uganda.",
    )

    # ─────────────────────────────────────────────
    # TITLES
    # ─────────────────────────────────────────────
    print("🏆  Seeding titles…")

    db.add(models.Title(
        fighter_id=f_omondi.id,
        title_name="Kenya National Champion",
        governing_body="BFK",
        weight_class="Lightweight 60kg",
        won_date=date(2024,3,12),
        won_at_event_id=ev_nat_champs_2024.id,
        opponent_defeated="Hassan Mwalimu (15-3-0)",
        win_method="Unanimous Decision",
        successful_defences=1,
        is_active=True,
        notes="First Kenyan from Kisumu to hold the national lightweight title.",
    ))
    db.add(models.Title(
        fighter_id=f_chepkemoi.id,
        title_name="Kenya Women National Champion",
        governing_body="BFK",
        weight_class="Flyweight 51kg Women",
        won_date=date(2024,1,22),
        won_at_event_id=ev_nat_champs_2024.id,
        opponent_defeated="Eunice Aoko (6-2-0)",
        win_method="Unanimous Decision",
        successful_defences=1,
        is_active=True,
    ))
    db.add(models.Title(
        fighter_id=f_wanjiku.id,
        title_name="East & Central Africa Champion",
        governing_body="ABU",
        weight_class="Featherweight 57kg",
        won_date=date(2023,11,8),
        won_at_event_id=ev_title_wanjiku.id,
        opponent_defeated="John Banda (Uganda, 18-4-0)",
        win_method="Majority Decision",
        successful_defences=0,
        is_active=True,
        notes="Title defended once — draw vs Phillip Otieno (Sep 2024).",
    ))
    db.add(models.Title(
        fighter_id=f_mwangi.id,
        title_name="Kenya National Champion",
        governing_body="BFK",
        weight_class="Welterweight 67kg",
        won_date=date(2022,6,5),
        opponent_defeated="Dennis Kimani (12-3-0)",
        win_method="TKO Round 7",
        successful_defences=0,
        is_active=False,
        vacated_date=date(2024,4,1),
        vacated_reason="Mwangi moved to professional division. Title vacated per BFK Rule 9.1.",
    ))

    # ─────────────────────────────────────────────
    # SUSPENSIONS
    # ─────────────────────────────────────────────
    print("🚫  Seeding suspensions…")

    db.add(models.Suspension(
        fighter_id=f_njoroge.id,
        suspension_type=models.SuspensionTypeEnum.medical,
        reason="Mandatory post-TKO suspension following medical stoppage vs Mark Waweru (Bout #2407)",
        rule_reference="BFK Rule 4.8 — Mandatory 30-day hold after stoppage loss",
        start_date=date(2025,7,10),
        end_date=date(2025,8,9),
        imposed_by="Dr. James Kibuchi — BFK Medical Officer",
        approved_by="James Kariuki — BFK Administrator",
        conditions="Must complete full re-examination. BP must read below 130/85. Neurological clearance required.",
        related_bout_id=bout_2407.id,
        is_active=True,
    ))
    db.add(models.Suspension(
        fighter_id=f_ochieng.id,
        suspension_type=models.SuspensionTypeEnum.disciplinary,
        reason="Unsportsmanlike conduct — struck opponent after final bell and verbally abused referee at Kisumu Champs",
        rule_reference="BFK Disciplinary Code Section 7.2 — Serious Misconduct",
        start_date=date(2025,6,1),
        end_date=date(2025,9,1),
        imposed_by="BFK Disciplinary Committee",
        approved_by="BFK Executive Board",
        conditions="Written apology to referee and opponent. Mandatory sportsmanship course before reinstatement. Fine: KES 15,000.",
        fine_amount_kes=15000,
        is_active=True,
    ))
    db.add(models.Suspension(
        fighter_id=f_mutua.id,
        suspension_type=models.SuspensionTypeEnum.medical,
        reason="Mandatory post-KO suspension following KO loss (Rd 2) vs Samuel Wanjiku — Nairobi Pro Night",
        rule_reference="KPBC Rule 6.3 — 30-day mandatory hold after KO loss",
        start_date=date(2025,6,28),
        end_date=date(2025,7,27),
        imposed_by="Dr. Peter Odhiambo — KPBC Medical Officer",
        approved_by="KPBC Commissioner",
        conditions="Full neurological review. CT scan recommended before return.",
        related_bout_id=bout_2403.id,
        is_active=True,
    ))
    # Cleared suspension (historical)
    db.add(models.Suspension(
        fighter_id=f_waweru.id,
        suspension_type=models.SuspensionTypeEnum.medical,
        reason="Post-TKO 30-day mandatory hold after TKO loss",
        rule_reference="BFK Rule 4.8",
        start_date=date(2025,4,10),
        end_date=date(2025,5,10),
        imposed_by="Dr. James Kibuchi — BFK Medical Officer",
        approved_by="James Kariuki — BFK Administrator",
        conditions="Full medical examination before return.",
        is_active=False,
        lifted_date=date(2025,5,9),
        lifted_by="Dr. James Kibuchi",
    ))

    # ─────────────────────────────────────────────
    # MATCHMAKING POOL
    # ─────────────────────────────────────────────
    print("🎯  Seeding matchmaking pool…")

    pool_entries = [
        # fighter, wc, walk_around, avail_from, bout_type, pref_opp_level, notes
        (f_omondi,    wc_lw_m,   62.5, date(2025,8,1),
         models.PreferredBoutTypeEnum.title, "Advanced / Professional",
         "Targeting national title defence. Prefers 10-round bout minimum."),

        (f_chepkemoi, wc_fly_f,  52.8, date(2025,8,14),
         models.PreferredBoutTypeEnum.title_defence, "Advanced",
         "Open to BFK and IBA competition. Priority: Nairobi Open Championship."),

        (f_katana,    wc_fly_m,  53.0, date(2025,8,14),
         models.PreferredBoutTypeEnum.non_title, "Novice",
         "First county-level bout. Needs opponent with 1-3 bouts max."),

        (f_wanjiku,   wc_fth_pro, 59.2, date(2025,8,22),
         models.PreferredBoutTypeEnum.title_defence, "Professional",
         "ABU Title defence required by Nov 2025. KPBC event only."),

        (f_njeri,     wc_lw_f,   61.0, date(2025,8,14),
         models.PreferredBoutTypeEnum.non_title, "Intermediate",
         "Medical licence expires Aug 2025 — MUST renew before confirmation."),

        (f_mutiso,    wc_lw_m,   61.0, date(2025,8,1),
         models.PreferredBoutTypeEnum.non_title, "Advanced",
         "Looking for high-profile bout to earn title shot. Same event as Omondi ideal."),

        (f_achieng,   wc_fly_f,  52.0, date(2025,8,14),
         models.PreferredBoutTypeEnum.non_title, "Intermediate",
         "Available for women's card at Nairobi Open."),

        (f_waweru,    wc_ww_m,   68.5, date(2025,8,14),
         models.PreferredBoutTypeEnum.non_title, "Intermediate / Advanced",
         "Post-suspension return bout. Prefers amateur card."),
    ]

    for (fighter, wc, walk, avail, btype, pref, notes) in pool_entries:
        db.add(models.MatchmakingPool(
            fighter_id=fighter.id,
            weight_class_id=wc.id,
            available_for_match=True,
            preferred_bout_type=btype,
            preferred_opponent_level=pref,
            walk_around_weight_kg=walk,
            available_from=avail,
            target_event_id=ev_nrb_open.id,
            notes=notes,
        ))

    db.commit()
    print("\n✅  Seed complete!")
    print(f"   Weight classes : {db.query(models.WeightClass).count()}")
    print(f"   Clubs          : {db.query(models.Club).count()}")
    print(f"   Coaches        : {db.query(models.Coach).count()}")
    print(f"   Fighters       : {db.query(models.Fighter).count()}")
    print(f"   Bouts          : {db.query(models.Bout).count()}")
    print(f"   Events         : {db.query(models.Event).count()}")
    print(f"   Titles         : {db.query(models.Title).count()}")
    print(f"   Suspensions    : {db.query(models.Suspension).count()}")
    print(f"   Pool entries   : {db.query(models.MatchmakingPool).count()}")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        reset_db()
        seed(db)
    except Exception as e:
        db.rollback()
        print(f"\n❌  Seed failed: {e}")
        raise
    finally:
        db.close()
