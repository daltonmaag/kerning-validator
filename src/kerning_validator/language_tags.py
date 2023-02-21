# Based on https://github.com/harfbuzz/harfbuzz/blob/424f5f2c0d10596abc79d98bc165cd9e86680597/src/hb-ot-tag-table.hh
# Entries without a Language System Tag were dropped.
LANG_SYS_TAGS_TO_BCP47 = {
    "AFR ": "aa  ",
    "ABK ": "ab  ",
    "AFK ": "af  ",
    "AKA ": "fat ",
    "AMH ": "am  ",
    "ARG ": "an  ",
    "ARA ": "ssh ",
    "ASM ": "as  ",
    "AVR ": "av  ",
    "AYM ": "ayr ",
    "AZE ": "azj ",
    "BSH ": "ba  ",
    "BEL ": "be  ",
    "BGR ": "bg  ",
    "BIS ": "bi  ",
    "CPP ": "xmm ",
    "BMB ": "bm  ",
    "BEN ": "bn  ",
    "TIB ": "bo  ",
    "BRE ": "br  ",
    "BOS ": "sh  ",
    "CAT ": "ca  ",
    "CHE ": "ce  ",
    "CHA ": "ch  ",
    "COS ": "co  ",
    "CRE ": "cwd ",
    "CSY ": "cs  ",
    "CSL ": "cu  ",
    "CHU ": "cv  ",
    "WEL ": "cy  ",
    "DAN ": "da  ",
    "DEU ": "de  ",
    "DIV ": "dv  ",
    "DHV ": "dv  ",
    "DZN ": "adp ",
    "EWE ": "ee  ",
    "ELL ": "el  ",
    "ENG ": "en  ",
    "NTO ": "eo  ",
    "ESP ": "es  ",
    "ETI ": "ekk ",
    "EUQ ": "eu  ",
    "FAR ": "tnf ",
    "FUL ": "fuv ",
    "FIN ": "fi  ",
    "FJI ": "fj  ",
    "FOS ": "fo  ",
    "FRA ": "fr  ",
    "FRI ": "fy  ",
    "IRI ": "ga  ",
    "GAE ": "gd  ",
    "GAL ": "gl  ",
    "GUA ": "nhd ",
    "GUJ ": "gu  ",
    "MNX ": "gv  ",
    "HAU ": "ha  ",
    "IWR ": "iw  ",
    "HIN ": "hi  ",
    "HMO ": "ho  ",
    "HRV ": "sh  ",
    "HAI ": "ht  ",
    "HUN ": "hu  ",
    "HYE0": "hy  ",
    "HYE ": "hyw ",
    "HER ": "hz  ",
    "INA ": "ia  ",
    "IND ": "in  ",
    "MLY ": "zsm ",
    "ILE ": "ie  ",
    "IBO ": "ig  ",
    "YIM ": "ii  ",
    "IPK ": "esk ",
    "IDO ": "io  ",
    "ISL ": "is  ",
    "ITA ": "it  ",
    "INU ": "ikt ",
    "INUK": "ike ",
    "JAN ": "ja  ",
    "JII ": "yih ",
    "JAV ": "jw  ",
    "KAT ": "ka  ",
    "KON0": "ldi ",
    "KIK ": "ki  ",
    "KUA ": "kj  ",
    "KAZ ": "kk  ",
    "GRN ": "kl  ",
    "KHM ": "km  ",
    "KAN ": "kn  ",
    "KOR ": "ko  ",
    "KOH ": "okm ",
    "KNR ": "krt ",
    "KSH ": "ks  ",
    "KUR ": "sdh ",
    "KOM ": "kpv ",
    "COR ": "kw  ",
    "KIR ": "ky  ",
    "LAT ": "la  ",
    "LTZ ": "lb  ",
    "LUG ": "lg  ",
    "LIM ": "li  ",
    "LIN ": "ln  ",
    "LAO ": "lo  ",
    "LTH ": "lt  ",
    "LUB ": "lu  ",
    "LVI ": "lvs ",
    "MLG ": "xmw ",
    "MAH ": "mh  ",
    "MRI ": "mi  ",
    "MKD ": "mk  ",
    "MAL ": "ml  ",
    "MLR ": "ml  ",
    "MNG ": "mvf ",
    "MOL ": "mo  ",
    "ROM ": "ro  ",
    "MAR ": "mr  ",
    "MTS ": "mt  ",
    "BRM ": "my  ",
    "NAU ": "na  ",
    "NOR ": "no  ",
    "NDB ": "nr  ",
    "NEP ": "npi ",
    "NDG ": "ng  ",
    "NLD ": "nl  ",
    "NYN ": "nn  ",
    "NAV ": "nv  ",
    "ATH ": "xup ",
    "CHI ": "ny  ",
    "OCI ": "oc  ",
    "OJB ": "otw ",
    "ORO ": "orc ",
    "ORI ": "spv ",
    "OSS ": "os  ",
    "PAN ": "pa  ",
    "PAL ": "pi  ",
    "PLK ": "pl  ",
    "PAS ": "pst ",
    "PTG ": "pt  ",
    "QUZ ": "qxw ",
    "RMS ": "rm  ",
    "RUN ": "rn  ",
    "RUS ": "ru  ",
    "RUA ": "rw  ",
    "SAN ": "sa  ",
    "SRD ": "sro ",
    "SND ": "sd  ",
    "NSM ": "se  ",
    "SGO ": "sg  ",
    "SRB ": "cnr ",
    "SNH ": "si  ",
    "SKY ": "sk  ",
    "SLV ": "sl  ",
    "SMO ": "sm  ",
    "SNA0": "sn  ",
    "SML ": "so  ",
    "SQI ": "als ",
    "SWZ ": "ss  ",
    "SOT ": "st  ",
    "SUN ": "su  ",
    "SVE ": "sv  ",
    "SWK ": "swh ",
    "TAM ": "ta  ",
    "TEL ": "te  ",
    "TAJ ": "tg  ",
    "THA ": "th  ",
    "TGY ": "ti  ",
    "TKM ": "tk  ",
    "TGL ": "tl  ",
    "TNA ": "tn  ",
    "TGN ": "to  ",
    "TRK ": "tr  ",
    "TSG ": "ts  ",
    "TAT ": "tt  ",
    "TWI ": "tw  ",
    "THT ": "ty  ",
    "UYG ": "ug  ",
    "UKR ": "uk  ",
    "URD ": "ur  ",
    "UZB ": "uzs ",
    "VEN ": "ve  ",
    "VIT ": "vi  ",
    "VOL ": "vo  ",
    "WLN ": "wa  ",
    "WLF ": "wo  ",
    "XHS ": "xh  ",
    "YBA ": "yo  ",
    "ZHA ": "zzj ",
    "ZHS ": "wuu ",
    "ZUL ": "zu  ",
    "ABA ": "abq ",
    "FAN ": "acf ",
    "ACR ": "acr ",
    "MYN ": "yua ",
    "DNG ": "ada ",
    "AGW ": "ahg ",
    "SWA ": "aii ",
    "SYR ": "tru ",
    "ARI ": "aiw ",
    "AKB ": "akb ",
    "BTK ": "btz ",
    "HBN ": "amf ",
    "MAP ": "arn ",
    "MOR ": "ary ",
    "RCR ": "atj ",
    "ALT ": "atv ",
    "BBR ": "zgh ",
    "AZB ": "azb ",
    "NAH ": "nuz ",
    "BAD0": "zmz ",
    "BML ": "ybb ",
    "BLI ": "bgp ",
    "BBC ": "bbc ",
    "BAU ": "bci ",
    "BIK ": "ubl ",
    "BCH ": "bcq ",
    "BTI ": "mct ",
    "BAD ": "bfq ",
    "BLT ": "bft ",
    "LAH ": "bfu ",
    "BAG ": "ppa ",
    "BGQ ": "bgq ",
    "RAJ ": "wbr ",
    "QIN ": "zyp ",
    "BHI ": "bhb ",
    "EDO ": "bin ",
    "BLN ": "ble ",
    "BKF ": "bla ",
    "IBA ": "snb ",
    "BLK ": "blk ",
    "KRN ": "wea ",
    "LRC ": "zum ",
    "BRI ": "bra ",
    "BTD ": "btd ",
    "BTM ": "btm ",
    "BTS ": "bts ",
    "BTX ": "btx ",
    "BTZ ": "btz ",
    "LUH ": "rag ",
    "RBU ": "bxr ",
    "BIL ": "byn ",
    "BYV ": "byv ",
    "CRR ": "crx ",
    "CAK ": "cak ",
    "CBK ": "cbk ",
    "CCHN": "cvn ",
    "ARK ": "ybd ",
    "HAL ": "flm ",
    "CHK0": "chk ",
    "HMA ": "mrj ",
    "LMA ": "mhr ",
    "CHP ": "chp ",
    "SAY ": "chp ",
    "CHK ": "ckt ",
    "HMN ": "sfm ",
    "QUH ": "qus ",
    "CRT ": "crh ",
    "ECR ": "crl ",
    "YCR ": "crl ",
    "WCR ": "crk ",
    "MCR ": "crm ",
    "LCR ": "crm ",
    "NCR ": "csw ",
    "NHC ": "csw ",
    "DCR ": "cwd ",
    "TCR ": "cwd ",
    "NIS ": "tgj ",
    "SLA ": "xsl ",
    "DGO ": "dgo ",
    "DGR ": "xnr ",
    "MAW ": "wry ",
    "DNK ": "dks ",
    "DIQ ": "diq ",
    "ZZA ": "kiu ",
    "DJR ": "dje ",
    "DJR0": "djr ",
    "DUN ": "dng ",
    "DRI ": "tnf ",
    "LSB ": "dsb ",
    "KUI ": "uki ",
    "DUJ ": "dwy ",
    "JUL ": "dyu ",
    "EMK ": "emk ",
    "MNK ": "myq ",
    "KAL ": "tuy ",
    "FNE ": "enf ",
    "TNE ": "enh ",
    "GON ": "wsg ",
    "EVN ": "eve ",
    "EVK ": "evn ",
    "FAN0": "fan ",
    "FAT ": "fat ",
    "PIL ": "fil ",
    "FMP ": "fmp ",
    "FTA ": "fuf ",
    "FRL ": "fur ",
    "FUV ": "fuv ",
    "GAD ": "gaa ",
    "GAW ": "gbm ",
    "GIL0": "gil ",
    "GKP ": "gkp ",
    "KPL ": "xpe ",
    "NAN ": "gld ",
    "KOK ": "knn ",
    "GRO ": "grt ",
    "SOG ": "gru ",
    "ALS ": "gsw ",
    "GMZ ": "guk ",
    "HAI0": "hdn ",
    "HRI ": "har ",
    "HMD ": "hmd ",
    "HMZ ": "hmz ",
    "CHH ": "hne ",
    "HND ": "hno ",
    "HO  ": "hoc ",
    "HAR ": "hoj ",
    "USB ": "hsb ",
    "IJO ": "orr ",
    "EBI ": "igb ",
    "ING ": "inh ",
    "JAM ": "jam ",
    "KRK ": "kaa ",
    "KAB0": "kab ",
    "KMB ": "kam ",
    "KAB ": "kbd ",
    "KHK ": "kca ",
    "KHS ": "kca ",
    "KHV ": "kca ",
    "KRM ": "kdr ",
    "KUY ": "kdt ",
    "KEA ": "kea ",
    "KEK ": "kek ",
    "KKN ": "kex ",
    "KOD ": "kfa ",
    "KAC ": "kfr ",
    "KUL ": "kfx ",
    "KMN ": "kfy ",
    "KSI ": "kha ",
    "XBD ": "khb ",
    "KHT ": "kht ",
    "KHN ": "kht ",
    "KIU ": "kiu ",
    "KHA ": "kjh ",
    "KJP ": "kjp ",
    "MBN ": "smd ",
    "KMO ": "kmw ",
    "KOP ": "koi ",
    "KOZ ": "kpv ",
    "KYK ": "kpy ",
    "KIS ": "kss ",
    "KRT ": "kqy ",
    "KAR ": "krc ",
    "BAL ": "krc ",
    "KRI ": "kri ",
    "KUU ": "kxl ",
    "KSH0": "ksh ",
    "KSW ": "ksw ",
    "KEB ": "ktb ",
    "KON ": "ktu ",
    "KMS ": "kxc ",
    "KYU ": "kyu ",
    "JUD ": "lad ",
    "LAK ": "lbe ",
    "LDK ": "lbj ",
    "LMB ": "lif ",
    "LAD ": "lld ",
    "LAM ": "lmn ",
    "MIZ ": "lus ",
    "ZHT ": "lzh ",
    "LAZ ": "lzz ",
    "MTH ": "mai ",
    "MKR ": "mak ",
    "MAM ": "mam ",
    "MOK ": "mdf ",
    "MLE ": "mdy ",
    "MDE ": "men ",
    "MFA ": "mfa ",
    "MFE ": "mfe ",
    "MIN ": "min ",
    "MLN ": "mlq ",
    "MCH ": "mnc ",
    "MND ": "mnk ",
    "MAN ": "mns ",
    "MON ": "mnw ",
    "MONT": "mnw ",
    "MAJ ": "mpe ",
    "MWW ": "mww ",
    "MEN ": "mym ",
    "ERZ ": "myv ",
    "NAG ": "nag ",
    "LMW ": "ngl ",
    "SXT ": "xnq ",
    "GIL ": "niv ",
    "NTA ": "nod ",
    "NKO ": "nqo ",
    "NAS ": "nsk ",
    "NKL ": "nyn ",
    "OCR ": "ojs ",
    "PAP0": "pap ",
    "PLG ": "rbb ",
    "PIH ": "pih ",
    "PAP ": "plp ",
    "POH ": "poh ",
    "PWO ": "pwo ",
    "QWH ": "qxw ",
    "QUC ": "quc ",
    "QVI ": "qxr ",
    "RIF ": "rif ",
    "ROY ": "rom ",
    "RMY ": "rmy ",
    "RSY ": "rue ",
    "YAK ": "sah ",
    "PAA ": "sam ",
    "SAD ": "sck ",
    "SCS ": "scs ",
    "SNA ": "seh ",
    "SFM ": "sfm ",
    "CHG ": "sgw ",
    "SHI ": "shi ",
    "KSM ": "sjd ",
    "SIB ": "sjo ",
    "SRK ": "skr ",
    "SSM ": "sma ",
    "LSM ": "smj ",
    "ISM ": "smn ",
    "SKS ": "sms ",
    "SIG ": "xst ",
    "SUR ": "suq ",
    "CMR ": "zdj ",
    "TMH ": "ttq ",
    "TUL ": "tcy ",
    "TMN ": "tem ",
    "TGR ": "tig ",
    "TOD0": "tod ",
    "TNG ": "toi ",
    "TPI ": "tpi ",
    "TUA ": "tru ",
    "TUV ": "tyv ",
    "TZM ": "tzm ",
    "TZO ": "tzo ",
    "MUN ": "unr ",
    "FLE ": "vls ",
    "MAK ": "vmw ",
    "WA  ": "wbm ",
    "WAG ": "wbr ",
    "KLM ": "xal ",
    "TOD ": "xwo ",
    "SEK ": "xan ",
    "XPE ": "xpe ",
    "SSL ": "xsl ",
    "ZHH ": "yue ",
    "ZGH ": "zgh ",
    "ZND ": "zne ",
}