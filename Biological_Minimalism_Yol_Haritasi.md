# BIOLOGICAL MINIMALISM
### Proje Yol Haritası ve Karar Dosyası

**77. Uluslararası Astronotik Kongresi (IAC 2026) — Antalya, Türkiye**
*Interactive Presentation · IAF/IAA Space Life Sciences Symposium (A1)*
Sunum Tarihi: 5–9 Ekim 2026
Haydarpaşa Lisesi Ekibi — F. Atila, E. H. Sünbül, I. Y. Virdil, P. Özdemir

> Bu dosya, projenin temelinden IAC sunumuna kadar olan tüm süreci tek bir yerde toplar. Jüri, ekip üyesi, yatırımcı veya bu konuya yabancı biri — bu dosyayı okuyan herkes projeyi, kararların gerekçesini ve yol haritasını buradan anlayabilir.

> ⚠️ **TARİHSEL PLANLAMA BELGESİ (Day-0/1 tasarım hipotezi).** Bu dosya projenin
> *özgün* çerçevesini kayıt altına alır ve provenans için korunmaktadır. Bazı fikirler,
> yürürlükteki kanıta-dayalı metodoloji tarafından **güncellenmiştir/aşılmıştır**:
> - "Yalnızca dört sensör" (EEG/PPG/sıcaklık/BioZ) **tarihsel bir tasarım hipotezidir**,
>   doğrulanmış veya seçilmiş minimal bir küme değildir. Güncel mimari karar durumu:
>   **`NOT_READY`**.
> - "%90 azaltım" gibi hedefler ve tek-seed "%23" IMU faydası **tarihsel** değerlerdir;
>   tekrarlanan çok-seed IMU faydası **≈%20,6**'dır. Bu proje **sahte kesinlik üretmeyi
>   reddeder**: toplam sistem gücü/kütlesi/BOM gibi bilinmeyenler `null` bırakılır.
> - IDI (Bilgi Yoğunluğu İndeksi) **önerilmiş fakat benimsenmemiş** bir kavramdır.
>
> **Güncel doğruluk kaynağı:** kök dizindeki `README.md`, araştırma API'si
> (`backend/app/research/`) ve `results/` içindeki değişmez artefaktlar.

---

## 1. Proje Nedir? (Herkesin Anlayacağı Dilde)

Uzay görevlerinde (Ay, Mars, Uzay İstasyonu) astronotların sağlığı genelde vücuda takılan çok sayıda sensörle (12 taneye kadar) takip ediliyor. Ama bu yaklaşımın gizli bir maliyeti var: makalede belirtildiği üzere 12 sensörlü bir kurulum, ciltte %30 daha fazla tahriş ve %15 daha fazla bilişsel yük yaratıyor — ayrıca ağırlık ve güç tüketimini artırıyor.

"Biological Minimalism" fikri şu: sensör sayısını 4'e indir (kablosuz EEG, PPG/nabız-oksijen sensörü, deri sıcaklığı sensörü, bio-empedans/vücut sıvı sensörü), ama yapay zekayla bu az veriyi öyle akıllıca işle ki sanki 12 sensör varmış gibi zengin, güvenilir bilgi üret.

**Nasıl çalışıyor?**

- **CNN (Convolutional Neural Network):** Her sensörden gelen ham sinyalden önemli özellikleri çıkarır.
- **RNN + Transformer:** Bu 4 sensörün verisini zaman içinde birleştirir (sensor fusion).
- **Biological Digital Twin:** Her astronot için kişiye özel bir "dijital ikiz" oluşturur — kişinin normal halini öğrenir, sapmaları (stres, yorgunluk, hastalık belirtisi) erken fark eder.

**Ne tahmin ediyor?**
Stres/otonomik denge, bilişsel yük, yorgunluk, uyku/sirkadiyen ritim, kalp-damar sağlığı, kansız tansiyon, solunum ve vücuttaki sıvı kaymaları (uzayda ciddi bir risk).

**Neden önemli?**
Yer kontrolüne bağımlılığı azaltıp astronotun kendi kendine sağlık takibi yapmasını sağlıyor. Ayrıca afet bölgeleri, kutup keşifleri, askeri operasyonlar ve uzak bölge sağlık hizmetleri gibi Dünya uygulamalarına da taşınabilir.

> **Özetle:** Az sensör + akıllı yapay zeka = çok sensörle aynı sonuç, ama daha rahat, daha hafif, daha az güç tüketen bir sistem.

---

## 2. Parametre Bazında Ölçüm Yöntemi: Geleneksel vs. Biological Minimalism

Aşağıdaki tablo, her bir fizyolojik parametrenin geleneksel yöntemle mi yoksa Biological Minimalism yaklaşımıyla mı, hangi cihaz ve hangi teknikle ölçüldüğünü gösterir. Bu tablo, "4 sensörle 12 sensörün işini nasıl yapıyorsunuz?" sorusuna en somut, en teknik cevaptır — jüri karşısında en güçlü kanıt parçalarından biridir.

| Parametre | Geleneksel Yöntem | Biological Minimalism |
|---|---|---|
| Stres Analizi | Kortizol Ölçümü — Metot: Düzenli tükürük analizi | Kuru Elektrotlu EEG Cihazı — Metot: Alpha ve Beta dalgalarının analizi |
| Bilişsel Yük | Çok Kanallı (32-64) Islak Elektrotlu EEG Cihazı — Metot: Uzun süreli ölçüm ve uzman analizi | Kuru Elektrotlu EEG Cihazı — Metot: Alpha ve Theta dalgalarının analizi |
| Sirkadiyen Ritim ve Uyku Kalitesi | Polisomnografi — Metot: Hastane ortamında kafa ve vücuttan alınan verilerle ölçülür ya da hiç ölçülmez | Kuru Elektrotlu EEG Cihazı + Termistör — Metot: Delta ve Theta dalgalarıyla REM ve derin uyku analizi + vücut sıcaklık analizi |
| Nabız | Göğüs EKG Bantları + Parmak Ucu Mandallı Oksimetre — Metot: Elektriksel ve optik ölçüm | PPG Cihazı — Metot: Sinyal dalgalarının tepe noktaları kalp atışıdır |
| Oksijen Doygunluğu | Göğüs EKG Bantları + Parmak Ucu Mandallı Oksimetre — Metot: Elektriksel ve optik ölçüm | PPG Cihazı — Metot: Kırmızı ve kızılötesi dalgaların emilme oranı farkları |
| Tansiyon | Tansiyon Manşonu (Sfigmomanometre) — Metot: Klasik ölçüm | PPG Cihazı — Metot: Sinyal dalgalarının diklik ve geri dönüş hızları, AI ile "Pulse Arrival Time" verisinden yola çıkarak tahmin edilir |
| Solunum Hızı | Göğüs Kafesi Kemeri (Respirasyon Kemeri) — Metot: Göğüs genişlemesini ölçer | PPG Cihazı — Metot: Kalp ritminde oluşan RSA etkisini AI ayıklayarak solunum hızını ölçer |
| Vücut Isısı | Termistör — Metot: Diğer sensörler dışında vücuda konularak yer kaplar | Termistör — Metot: PPG'nin yanına yerleştirilen sensörle ayrıca yer kaplamaz |
| Fluid Shift | MRI / OCT — Metot: Karmaşık ve giyilebilir olmayan ölçüm ve analiz cihazları | Biyo-empedans Elektrotları — Metot: Hafif elektrik akımlarıyla dokudaki elektrik direnci ölçülür ve AI ile düzenli analiz edilir |
| Enfeksiyon Takibi | Klinik çalışmalar — Not: Giyilebilir teknolojilerle enfeksiyon takibi bugün için doğrudan yapılamıyor | EEG Cihazı + Termistör — Metot: Bilişsel performans düşerken vücut sıcaklığı artıyorsa, bu bir enfeksiyon başlangıç belirtisi olarak değerlendirilir |

> **Not:** "Enfeksiyon Takibi" satırındaki geleneksel yöntem notu, kaynak dosyada birkaç satırda tekrar eden bir ifadeydi; burada sadece ait olduğu düşünülen tek satıra yerleştirildi. Ekip bunu gözden geçirmelidir.

---

## 3. IAC Sunum Formatı — Ne Bekleniyor?

IAF'ın resmi tanımına göre "Interactive Presentation" formatı bir fiziksel demo standı DEĞİLDİR. Şunları içerir:

- Sunum, kongre haftası (5–9 Ekim) boyunca bir ekranda dijital olarak sürekli gösterilir.
- Ekibe 8–10 dakikalık özel bir zaman dilimi veriliyor; bu sürede katılımcılarla birebir etkileşim kurulur.
- PowerPoint, gömülü linkler, resim, ses ve video klipler kullanılabilir.
- En az bir yazarın Antalya'da bizzat bulunması ve sunumu yapması zorunludur.

> **Sonuç:** Fiziksel donanımı Antalya'ya taşımak ZORUNLU DEĞİL. Asıl teslim edilecek şey; iyi kurgulanmış bir slayt/ekran gösterimi + içine gömülü demo videosu + 8-10 dakikalık canlı konuşmadır. Bu, MVP kapsamını önemli ölçüde kolaylaştırır.

---

## 4. MVP Kapsamı — Neyi İnşa Ediyoruz?

### 4.1 Ana MVP: Yazılım Öncelikli Dashboard

Açık veri setleri üzerinde çalışan gerçek bir makine öğrenmesi hattı + "Biological Digital Twin" kavramını gösteren interaktif bir dashboard. Dashboard, kaydedilmiş sensör verisini canlıymış gibi oynatır, dijital ikizin kişiye özel bazalini öğrenmesini ve sapmaları işaretlemesini gösterir.

### 4.2 Stretch Hedef: Canlı EEG Demosu

Ekibin EEG cihazı olduğu ve bunun okulda, resmi bir araştırma deneği değil sistem geliştirme/iç test amaçlı kullanılabileceği netleşti. Bu, IAC'deki 8-10 dakikalık canlı sunumun içine, modelin ekip üyesi üzerinde gerçek zamanlı çalıştığını gösteren kısa (30 saniye–1 dakika) bir "sahne anı" eklenmesini mümkün kılıyor.

> **Çerçeveleme uyarısı:** Bu iç test asla "klinik doğrulama" veya "araştırma denek grubu" olarak sunulmamalı. Doğru dil: "Sistem geliştirme ve doğrulama amaçlı iç test (internal developer testing); istatistiksel bir doğrulama kohortu değil, zero-shot genelleme yeteneğinin niteliksel bir kanıtıdır."

### 4.3 Dashboard Fonksiyonel Spesifikasyonu — MVP bittiğinde tam olarak ne çalışıyor olacak?

**Sahne arkası (ML hattı):**

1. **Veri:** WESAD / STEW / PulseDB / NASA OSDR'den alınan, önceden kaydedilmiş sinyaller (EEG, PPG, termistör, bio-empedans).
2. **CNN:** Her sinyalden özellik çıkarır.
3. **RNN + Transformer füzyon:** Modaliteleri birleştirip tek bir fizyolojik durum tahmini üretir.
4. **Zero-shot meta-learning + Euclidean Alignment:** Model hiç görmediği bir kişide de mantıklı tahmin yapar.
5. **Digital Twin mantığı:** Kişinin bazalini öğrenir, sapmaları işaretler.

**Kullanıcının göreceği panel yapısı:**

- **Canlı İzleme Paneli:** Seçilen bir denek için kaydedilmiş sinyal gerçek-zamanlıymış gibi akar; ham sinyal grafikleri (EEG dalga formu, PPG nabız dalgası, sıcaklık eğrisi) ve türetilmiş fizyolojik durumlar (stres, bilişsel yük, tahmini tansiyon, solunum hızı) gösterge olarak güncellenir.
- **Digital Twin Paneli:** Kişinin öğrenilmiş bazali referans çizgisi olarak gösterilir; sapma olduğunda görsel uyarı tetiklenir.
- **Karşılaştırma Paneli:** "4 sensörle minimal sistem" vs. "simüle edilmiş 12 sensörlü geleneksel sistem" yan yana; makalenin ana iddiasının canlı kanıtı.
- **Dayanıklılık Testi Paneli:** Bir düğmeyle gürültü/hareket artefaktı/sensör kaybı enjekte edilip sistemin tepkisi gösterilir.
- **Kişi/Senaryo Seçici:** Farklı deneklere veya OSDR'den bir bed-rest senaryosuna geçiş — zero-shot genelleme iddiasının gösterimi.

**Kapsam sınırı (MVP neyi yapmayacak):**

- Gerçek zamanlı, gerçek bir insandan canlı veri toplamayacak (EEG stretch demosu hariç).
- Klinik olarak doğrulanmış bir tıbbi cihaz değil — bir araştırma/kavram-kanıtı aracı.
- Gerçek astronot verisiyle test edilmemiş olacak (Bölüm 6'daki sınırlama).

---

## 5. Veri Seti Haritası

| Hedef | Sensör | Veri Seti | Durum |
|---|---|---|---|
| Stres / otonomik denge | EDA, ECG, EMG, solunum, sıcaklık, PPG | WESAD | 🟢 Güçlü |
| Bilişsel yük | EEG | STEW (Simultaneous Task EEG Workload) | 🟢 Güçlü |
| Kansız tansiyon (cuffless BP) | PPG + ECG | MIMIC-II/III türevi (PulseDB, UCI CLBP) | 🟢 Çok güçlü |
| Solunum, uyku/sirkadiyen ritim | Termistor, solunum | WESAD (kısmi) + PhysioNet Sleep-EDF | 🟡 Orta |
| Vücut sıvı kayması (fluid shift) | Bio-empedans | NASA OSDR — head-down tilt bed rest / dry immersion | 🟢 Astronot-analog / en değerli kaynak |

**Neden NASA OSDR özellikle değerli?**
NASA Open Science Data Repository, gerçek uzay uçuşu ve uzay-benzeri koşullarda (ESA/DLR gibi kurumların head-down tilt bed rest ve dry immersion çalışmaları) toplanmış fizyolojik, fenotipik, davranışsal ve çevresel telemetri verilerini barındırıyor. Bu, makalenin bahsettiği "simulated spaceflight analog conditions" kavramının literatürde kabul görmüş, gerçek karşılığıdır — jüri karşısında büyük bir kredibilite avantajı sağlar.

---

## 6. Sınırlama: Veri Setleri Astronotlara Uygun mu?

Dürüst cevap: Kısmen. Bu, uzay biyomedikal araştırmalarının tamamının yaşadığı, iyi bilinen bir sorundur ("domain gap").

| Veri Seti Grubu | Uyumsuzluk Nedeni | Risk Seviyesi |
|---|---|---|
| WESAD, STEW, PulseDB/MIMIC | Genel sivil nüfus / hastane hastaları; mikrogravite, radyasyon, izolasyon yok | 🔴 Yüksek |
| NASA OSDR (bed rest / dry immersion) | Gerçek astronot-analog protokol, ama az veri hacmi | 🟡 Orta |

**Çözüm çerçevesi (makalede ve sunumda kullanılacak dil):**

- **Şeffaflık:** Net bir "Sınırlamalar" bölümü/slaydı olacak: "Modeller genel popülasyon ve yer-tabanlı analog verilerle eğitildi/valide edildi; gerçek astronot kohortu üzerinde doğrulama gelecek çalışma kapsamındadır."
- Digital Twin mimarisi zaten bu sorunu kısmen çözüyor: genel veri setiyle ön-eğitim + bireysel kalibrasyon katmanıyla domain gap kapatılıyor.
- Fluid shift (OSDR) iddiası güvenle savunulur; stres/bilişsel yük (WESAD/STEW) iddiaları "genellenebilirlik varsayımı" olarak temkinli sunulur.

---

## 7. Kalibrasyon Yöntemi (Literatür Destekli)

Ekibin EEG donanımı var, ancak resmi etik kurul onayı olmadan yeni araştırma-denek verisi toplanamıyor. Bu nedenle 3 katmanlı, tamamen etik-güvenli bir kalibrasyon stratejisi seçildi:

**Katman 1 — Euclidean Alignment (EA):** Derin öğrenme gerektirmeyen, sinyal kovaryans istatistiklerini hizalayan basit ve hızlı bir alan-uyumlaştırma tekniği. Veri setleri arası (örn. STEW'den kendi mimarinize) hizalama için kullanılır. Kodlaması 1-2 gün sürer.

**Katman 2 — Zero-shot / Zero-calibration Subject-Independent Meta-Learning:** Model, hiç görmediği bir kişide de çalışacak şekilde meta-öğrenme ile eğitilir — yeni insan verisi toplamaya GEREK KALMAZ. Bu, etik kısıtı tamamen aşan ana omurga yöntemdir.

**Katman 3 — Ekip İçi EEG Doğrulama (Stretch):** Okulda, resmi araştırma deneği olmadan, sistem geliştirme/test amaçlı ekip üyesi EEG verisiyle modelin zero-shot tahminlerinin niteliksel bir "canlı kanıtı" gösterilir. Bu, istatistiksel doğrulama değil, kavramın çalıştığının gösterimidir.

> **Sunumda özet cümle:** "Etik kısıtlar nedeniyle yeni araştırma-denek verisi toplamadık; bunun yerine literatürdeki zero-shot subject-independent meta-learning ve Euclidean Alignment yaklaşımlarını benimsedik, ardından ekip içi geliştirme testiyle kavramı niteliksel olarak doğruladık."

---

## 8. Farklı Perspektiflerden Bakış

### 8.1 Jüri Perspektifi

Jüri neye bakar: bilimsel titizlik, iddiaların kanıta dayalı olup olmadığı, yenilik, sunum netliği.

**Olası sorular ve hazır cevaplar**

| Olası Soru | Hazır Cevap |
|---|---|
| %90 azaltım / %30-%15 rakamları nereden geliyor? | Literatür varsayımı olarak sunulacak, kendi karşılaştırmalı testimizle (Hafta 4) desteklenecek. Kaynak gösterilecek. |
| Bu gerçek astronot verisi mi? | Hayır; açık veri setleri (WESAD, STEW, PulseDB) + NASA OSDR astronot-analog verisi kullanıldı. Bu açıkça belirtilecek. |
| Modeliniz yeni bir kişide çalışır mı, yoksa ezber mi yapıyor? | Zero-shot subject-independent meta-learning ile eğitildi; ekip içi EEG testiyle niteliksel olarak gösterildi. |
| Neden fiziksel bir prototip yok? | IAC Interactive Presentation formatı bunu gerektirmiyor; kaynaklarımızı bilimsel doğrulamaya (veri, model, sınırlamalar) yoğunlaştırdık. |

### 8.2 Ekip Üyesi Perspektifi

Ekip üyesi neye bakar: kendi görev tanımı, günlük iş akışı, ne zaman ne teslim edeceği.

- Her hafta net bir çıktı var (bkz. Bölüm 10 — Takvim); rolünüz ne olursa olsun haftanın sonunda gösterilecek somut bir şey olmalı.
- Roller net belirlenmiş durumda; bu dosyadaki haftalık "Odak" sütunu, kimin o hafta hangi işe ağırlık vereceğini gösterir — ekip içinde kendi rolünüze göre eşleştirin.
- Sorun/blokaj oluşursa (örn. veri seti erişim sorunu), o haftanın çıktısını küçültüp bir sonraki haftaya taşıyın; tüm planı bozmayın.

### 8.3 Yatırımcı / Sponsor Perspektifi

Yatırımcı neye bakar: ölçeklenebilirlik, pazar potansiyeli, maliyet-fayda mantığı.

- **Ölçeklenebilirlik:** Aynı mimari afet müdahalesi, kutup keşifleri, askeri operasyonlar ve uzak bölge sağlık hizmetlerine taşınabilir — uzay dışı pazar potansiyeli var.
- **Maliyet-fayda:** 12 sensörden 4 sensöre inmek, donanım ve güç maliyetini yaklaşık %90 azaltıyor (doğrulanacak iddia).
- **Risk:** Şu an TRL (Teknoloji Hazırlık Seviyesi) düşük — kavram/yazılım MVP aşamasında; gerçek donanım entegrasyonu ve klinik doğrulama sonraki adım olarak konumlandırılmalı.

### 8.4 Kullanıcı (Astronot) Perspektifi

Kullanıcı neye bakar: konfor, güven, kullanım kolaylığı.

- **Konfor:** 12 sensör yerine 4 sensör — daha az cilt teması, daha az rahatsızlık.
- **Güven:** Sistem yanlış alarm verirse (false positive) ya da gerçek bir sorunu kaçırırsa (false negative) astronot güvenini kaybeder; bu yüzden "sapma tespiti" eşik değerlerinin dikkatli ayarlanması gerektiği açıkça belirtilmeli.
- **Otonomi:** Yer kontrolüne bağımlılığı azaltması, uzun süreli/derin uzay görevlerinde (iletişim gecikmesi olan Mars gibi) kritik bir avantaj.

---

## 9. Proje Fazları: 0'dan Full-Fonksiyonlu MVP'ye

Bölüm 10'daki takvim "hangi hafta ne yapılıyor" sorusuna cevap veriyor. Bu bölüm ise "proje şu an hangi olgunluk seviyesinde, bir sonraki seviyeye geçmek için ne tamamlanmalı" sorusuna cevap veriyor. Her fazın net bir Çıkış Kriteri (o faz bittiğinde elde olması gereken somut şey) vardır — bir faz bu kriteri karşılamadan bir sonrakine geçilmemelidir.

| Faz | Adı | İlgili Hafta | Çıkış Kriteri (Özet) |
|---|---|---|---|
| Faz 0 | Temel Hazırlık | Hafta 1 | Veri setleri indirildi, kapsam (2-3 hedef durum) netleşti |
| Faz 1 | Veri Altyapısı & Baseline | Hafta 2 | Modalite başına çalışan baseline model + ilk doğruluk sayıları |
| Faz 2 | Füzyon & Kişiselleştirme | Hafta 3 | Çok-modaliteli füzyon modeli + EA kalibrasyonu çalışıyor |
| Faz 3 | Doğrulama & Sağlamlık | Hafta 4 | Minimal vs. tam sensör karşılaştırması + zero-shot entegrasyonu tamam |
| Faz 4 | Dashboard & Canlı Demo | Hafta 5 (ilk yarı) | Full-fonksiyonlu dashboard + demo videosu — **MVP TAMAM** |
| Faz 5 | Sunum Paketleme & Prova | Hafta 5 (ikinci yarı) + Son Günler | Slayt destesi + konuşma metni + prova tamam |

### Faz 0 — Temel Hazırlık
**Amaç:** Projenin geri kalanının üzerine kurulacağı zemini sağlamlaştırmak. Bu fazda kod yazılmaz — karar verilir.

**Ana Görevler**
- 2-3 hedef fizyolojik durumu seç (ör. bilişsel yük, otonomik denge, yorgunluk) — makaledeki tüm listeyi değil, gerçekçi bir alt kümeyi hedefle.
- WESAD, STEW, PulseDB, NASA OSDR veri setlerini indir ve klasör yapısını kur.
- "Spaceflight analog" stres senaryolarını tanımla (hareket artefaktı, gürültü enjeksiyonu, sensör kaybı simülasyonu).
- Geliştirme ortamını kur (Python, gerekli kütüphaneler, versiyon kontrolü).

> **Çıkış Kriteri:** Tüm veri setleri diskte, okunabilir durumda VE ekip hedef 2-3 fizyolojik duruma yazılı olarak karar vermiş durumda.

### Faz 1 — Veri Altyapısı & Baseline
**Amaç:** Ham sinyalden anlamlı özellik çıkarabilen ve basit bir tahmin yapabilen ilk çalışan parçayı üretmek.

**Ana Görevler**
- Veri ön işleme: filtreleme, segmentasyon, etiketleme (her veri setinin kendi formatına göre).
- Modalite başına CNN feature extraction (EEG için ayrı, PPG için ayrı, vb.).
- Tek-modaliteli baseline modeller eğit — bunlar sonradan "füzyon modelimiz baseline'dan daha iyi" iddiasının kıyaslama noktası olacak.

> **Çıkış Kriteri:** Her hedef fizyolojik durum için en az bir modalitede çalışan, ölçülebilir bir doğruluk skoru veren baseline model var.

### Faz 2 — Füzyon & Kişiselleştirme
**Amaç:** Tek tek modaliteleri birleştirip gerçek "Biological Digital Twin" mantığının çekirdeğini oluşturmak.

**Ana Görevler**
- RNN/Transformer füzyon katmanını kur — birden fazla modaliteyi zaman içinde birleştir.
- Euclidean Alignment (EA) uygula — veri setleri arası dağılım farkını azalt.
- Basit kişiselleştirme mantığı: kişi-bazlı bazal kalibrasyon + sapma tespiti (Digital Twin'in ilk çalışan versiyonu).
- Dashboard'un iskeletini (boş arayüz + veri bağlantısı) kur — henüz "full-fonksiyon" değil.

> **Çıkış Kriteri:** En az iki modaliteyi birlikte işleyen bir model var VE bu model Faz 1'deki tek-modaliteli baseline'dan ölçülebilir şekilde daha iyi (veya en azından farklı bir değer katıyor).

### Faz 3 — Doğrulama & Sağlamlık
**Amaç:** Makaledeki "minimal sensör = tam sensörle eşdeğer performans" iddiasının kendi verinizle üretilmiş kanıtını oluşturmak.

**Ana Görevler**
- Karşılaştırmalı test: minimal sensör seti (4) vs. simüle edilmiş tam set (12) senaryosu.
- Gürültü, hareket artefaktı ve sensör kaybı enjekte ederek dayanıklılık (robustness) testi yap.
- Zero-shot subject-independent meta-learning yaklaşımını entegre et — modelin hiç görmediği kişide de çalıştığını göster.
- "%90 azaltım", doğruluk ve dayanıklılık rakamlarını kendi test sonuçlarınızla üretin (literatürden kopyalamayın).

> **Çıkış Kriteri:** Minimal set ile tam set arasındaki performans farkını gösteren somut sayılar (tablo/grafik) elinizde var VE bu sayılar makale/sunumdaki iddiaları destekliyor ya da iddiaları gerçekçi şekilde güncelliyor.

### Faz 4 — Dashboard & Canlı Demo (MVP Tamamlanma Noktası)
**Amaç:** Şimdiye kadar üretilen tüm bileşenleri (veri, model, doğrulama) tek, izlenebilir ve etkileyici bir arayüzde birleştirmek. Proje bu fazın sonunda "full-fonksiyonlu MVP" sayılır.

**Ana Görevler**
- Dashboard'u tamamla: kaydedilmiş veriyi canlıymış gibi oynatma, Digital Twin'in bazal öğrenmesini ve sapma uyarılarını görselleştirme.
- Minimal set vs. tam set karşılaştırmasını dashboard içinde görsel olarak göster ("wow" etkisi burada).
- Dashboard'un ekran kaydını (demo videosu) al — bu, IAC'deki dijital ekran gösterimine gömülecek.
- Ekip içi EEG canlı testini bu fazda dene — sahne için provaya başla.

> **Çıkış Kriteri:** Dashboard'u projeye hiç dahil olmamış bir kişiye açıp "işte böyle çalışıyor" diyerek 2 dakikada anlatabiliyorsanız — bu, MVP'nin "full-fonksiyonlu" sayıldığı andır.

### Faz 5 — Sunum Paketleme & Prova
**Amaç:** Full-fonksiyonlu MVP'yi, IAC'nin dijital ekran + 8-10 dakikalık canlı sunum formatına uygun, ikna edici bir anlatıya dönüştürmek.

**Ana Görevler**
- Slayt destesini oluştur (ekranda sürekli gösterilecek format), demo videosunu göm.
- 8-10 dakikalık konuşma metnini yaz; Bölüm 8.1'deki olası jüri sorularına karşı cevapları ezberle.
- Tam prova yap (zamanlama dahil); offline yedekleri (USB, laptop yerel disk) hazırla.
- Lojistik: seyahat, konaklama, akreditasyon kontrolü.

> **Çıkış Kriteri:** Sunum, hiçbir ekip üyesinin canlı internete veya harici bir bağlantıya ihtiyaç duymadan, tamamen offline olarak eksiksiz gösterilebiliyor.

---

## 10. Basit Takvim (27 Ağustos – 9 Ekim 2026)

| Hafta | Tarih | Odak | Hafta Sonu Çıktısı |
|---|---|---|---|
| Hafta 1 | 27 Ağu – 2 Eyl | Kapsam netleştirme: 2-3 hedef fizyolojik durum seç, veri setlerini indir (WESAD, STEW, PulseDB, OSDR), "spaceflight analog" stres senaryolarını tanımla. | Seçilmiş veri setleri + net kapsam dokümanı |
| Hafta 2 | 3 – 9 Eyl | Veri ön işleme + modalite başına CNN feature extraction. Tek-modaliteli baseline modeller. | Çalışan baseline modeller + ilk doğruluk sayıları |
| Hafta 3 | 10 – 16 Eyl | RNN/Transformer füzyon katmanı. Euclidean Alignment uygulaması. Basit "digital twin" kişiselleştirme mantığı. Dashboard iskeleti. | Çalışan füzyon modeli + dashboard iskeleti |
| Hafta 4 | 17 – 23 Eyl | Karşılaştırmalı doğrulama (minimal set vs. tam set, gürültü/artefakt enjeksiyonu). Zero-shot meta-learning entegrasyonu. Dashboard'u demo'ya hazırla, ekran kaydı al. | "%90 azaltım" iddiasının kendi verimiz + demo videosu |
| Hafta 5 | 24 – 30 Eyl | Slayt destesi (ekranda gösterilecek format) + gömülü demo videosu. Ekip içi EEG canlı test/prova. 8-10 dakikalık konuşma metni. | Tam slayt destesi + EEG demo denemesi |
| Son Günler | 1 – 4 Eki | Tam prova (zamanlama dahil), yedek materyal (USB, offline video), lojistik (seyahat, konaklama, akreditasyon) kontrolü. | Prova tamamlanmış, çanta hazır |
| IAC Haftası | 5 – 9 Eki | Antalya'da sunum: dijital ekran gösterimi tüm hafta boyunca açık; 8-10 dakikalık canlı sunum + soru-cevap. | Sunum tamamlandı |

---

## 11. Riskler ve Çözümleri

| Risk | Etki | Çözüm |
|---|---|---|
| Veri seti indirme/işleme beklenenden uzun sürer | 🟡 Orta | Hafta 1'de tüm veri setlerini paralel indirin; WESAD ve STEW küçük boyutlu, hızlı başlanabilir. |
| Füzyon modeli (RNN+Transformer) beklenen doğruluğu vermez | 🔴 Yüksek | Basit bir baseline (ör. sadece CNN) her zaman yedek olarak hazır tutulsun; "karşılaştırmalı iyileşme" iddiası baseline'a göre kurulsun. |
| EEG iç testi sahnede teknik olarak çalışmaz (canlı demo riski) | 🔴 Yüksek | Canlı demonun önceden kaydedilmiş bir video yedeği HER ZAMAN slayt içine gömülü olsun; sahnede sorun çıkarsa videoya geçilsin. |
| Jüri "gerçek astronot verisi değil" eleştirisi yapar | 🟡 Orta | Bölüm 6'daki şeffaflık dilini birebir kullanın; bunu siz söylerseniz güçlü, jüri sorup siz savunursanız zayıf görünürsünüz. |
| Zaman yetişmez (5.5 hafta kısa) | 🔴 Yüksek | MVP kapsamı zaten yazılım-öncelikli ve gerçekçi olarak daraltıldı; bir hafta gecikirse önce "stretch" (EEG demo) hedefi feda edilsin, ana dashboard korunsun. |
| İnternet/teknik altyapı sorunu (Antalya'da) | 🟢 Düşük | Demo videosu ve slaytlar offline (USB + laptop yerel disk) olarak yedeklensin. |

---

## 12. Son Kontrol Listesi

- [ ] Hafta 1 sonunda: Veri setleri indirildi mi? Hedef 2-3 fizyolojik durum netleşti mi?
- [ ] Hafta 3 sonunda: Dashboard iskeleti bir başkasına gösterilebilir durumda mı?
- [ ] Hafta 4 sonunda: Karşılaştırmalı sayılar (minimal vs. tam sensör) elimizde mi?
- [ ] Hafta 5 sonunda: Slayt destesi + demo videosu + EEG canlı deneme + 8-10 dk konuşma metni tamam mı?
- [ ] Son günlerde: Offline yedekler, seyahat/akreditasyon, prova tamamlandı mı?

> Bu dosya, proje ilerledikçe güncellenmesi gereken canlı bir belgedir. Her hafta sonunda bu listeyi gözden geçirin.

---

## 13. Kaynakça

Bölüm 2'deki parametre karşılaştırma tablosu ve makaledeki teknik iddialar için kullanılan/kullanılabilecek literatür kaynakları aşağıda listelenmiştir.

- Liu, C., Chen, L., Ding, J., Huang, L., & Shangguan, D. (2026). Model–Data Hybrid Thermal Management and Health Monitoring of the Space Station Application Fluid Loop. *Results in Engineering*, 109387.
- Grigoriev, A. I., & Egorov, A. D. (1997). Medical monitoring in long-term space missions. *Advances in Space Biology and Medicine*, 6, 167-191.
- Gupta, R., & Ghosh, P. S. (2025). Advancements in health monitoring technologies for astronauts in deep space missions: A Review. *Life Sciences in Space Research*, 47, 190-196.
- Pool, S. L. (1975). Physiological Measurement Systems for Advanced Manned Space Missions. In *Advances in Biomedical Engineering* (pp. 151-215). Academic Press.
- DeVirgiliis, L., Goode, N. J., McDowell, K. W., English, K. L., Novo, R., Botros, V., ... & Ploutz-Snyder, L. L. (2025). Spaceflight and sport science: Physiological monitoring and countermeasures for the astronaut–athlete on Mars exploration missions. *Experimental Physiology*.
- Roda, A., Mirasoli, M., Guardigli, M., Zangheri, M., Caliceti, C., Calabria, D., & Simoni, P. (2018). Advanced biosensors for monitoring astronauts' health during long-duration space missions. *Biosensors and Bioelectronics*, 111, 18-26.
- Fei, D. Y., Zhao, X., Boanca, C., Hughes, E., Bai, O., Merrell, R., & Rafiq, A. (2010). A biomedical sensor system for real-time monitoring of astronauts' physiological parameters during extra-vehicular activities. *Computers in Biology and Medicine*, 40(7), 635-642.
- Mundt, C. W., Montgomery, K. N., Udoh, U. E., Barker, V. N., Thonier, G. C., Tellier, A. M., ... & Kovacs, G. T. (2005). A multiparameter wearable physiologic monitoring system for space and terrestrial applications. *IEEE Transactions on Information Technology in Biomedicine*, 9(3), 382-391.
- Baevsky, R. M., Petrov, V. M., & Chernikova, A. G. (1998). Regulation of autonomic nervous system in space and magnetic storms. *Advances in Space Research*, 22(2), 227-234.
- McCorry, L. K. (2007). Physiology of the autonomic nervous system. *American Journal of Pharmaceutical Education*, 71(4), 78.
- Kurt, B. Uzayda Zamanı Yakalamak: Sirkadiyen Ritim.
- Kaya, E. Ö., & Kaya, M. Fiziksel Aktivitenin Otonom Sinir Sistemi Üzerindeki Rolü: Vagus Siniri Perspektifinden Bakış. *Spor Bilimleri*, 89.
- Yaşa, Ö. Egzersiz ve Sinir Sistemi Arasındaki Nörobiyolojik İlişkinin İncelenmesi.
