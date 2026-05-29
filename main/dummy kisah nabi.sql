-- ============================================
-- DATA DUMMY KISAH NABI
-- ============================================

-- Insert Kisah Nabi
INSERT INTO kisah_nabi (prophet_name, total_read_count, main_cover, description, created_at, updated_at) VALUES
('Adam', 15234, 'kisah_nabi/covers/adam.jpg', 'Nabi Adam AS adalah manusia pertama yang diciptakan Allah SWT. Beliau adalah bapak seluruh umat manusia dan diturunkan ke bumi setelah memakan buah khuldi.', NOW(), NOW()),
('Idris', 8234, 'kisah_nabi/covers/idris.jpg', 'Nabi Idris AS dikenal sebagai nabi yang cerdas dan ahli dalam berbagai ilmu pengetahuan. Beliau adalah orang pertama yang menulis dengan pena.', NOW(), NOW()),
('Nuh', 45321, 'kisah_nabi/covers/nuh.jpg', 'Nabi Nuh AS diutus untuk kaumnya yang menyembah berhala. Beliau membangun kapal besar untuk menyelamatkan umat beriman dari banjir bandang.', NOW(), NOW()),
('Hud', 7234, 'kisah_nabi/covers/hud.jpg', E'Nabi Hud AS diutus untuk kaum ''Ad yang sombong dan kuat. Mereka ditimpa azab berupa angin topan yang dahsyat.', NOW(), NOW()),
('Saleh', 6345, 'kisah_nabi/covers/saleh.jpg', 'Nabi Saleh AS diutus untuk kaum Tsamud. Mukjizatnya adalah unta betina yang keluar dari batu besar.', NOW(), NOW()),
('Ibrahim', 67342, 'kisah_nabi/covers/ibrahim.jpg', 'Nabi Ibrahim AS adalah bapak para nabi. Beliau dikenal dengan keberaniannya menghancurkan berhala dan kesabarannya saat hendak disembelih.', NOW(), NOW()),
('Luth', 8234, 'kisah_nabi/covers/luth.jpg', 'Nabi Luth AS diutus untuk kaum Sodom yang melakukan perbuatan keji. Kaumnya ditimpa azab berupa hujan batu.', NOW(), NOW()),
('Ismail', 12345, 'kisah_nabi/covers/ismail.jpg', 'Nabi Ismail AS adalah putra Nabi Ibrahim yang hampir disembelih. Beliau membantu ayahnya membangun Ka''bah.', NOW(), NOW()),
('Ishaq', 9876, 'kisah_nabi/covers/ishaq.jpg', 'Nabi Ishaq AS adalah putra Nabi Ibrahim dari istrinya Sarah. Beliau menjadi nabi untuk kaumnya di Palestina.', NOW(), NOW()),
('Yaqub', 8765, 'kisah_nabi/covers/yaqub.jpg', 'Nabi Yaqub AS dikenal dengan kesedihannya yang mendalam karena kehilangan putranya, Nabi Yusuf. Beliau juga disebut Israel.', NOW(), NOW());


-- Insert Episode untuk setiap Kisah Nabi
-- Nabi Adam (kisah_nabi_id = 1)
INSERT INTO kisah_nabi_episode (kisah_nabi_id, title, description, doc_url, cover_url, "order", created_at) VALUES
(1, 'Penciptaan Nabi Adam AS', 'Allah SWT menciptakan Nabi Adam dari tanah liat kering yang diambil dari berbagai penjuru bumi. Kemudian ditiupkan ruh sehingga menjadilah manusia pertama.', 'https://storage.smarthijrah.com/kisah/adam/adam_episode1.pdf', 'https://storage.smarthijrah.com/kisah/adam/adam_cover1.jpg', 1, NOW()),
(1, 'Nabi Adam dan Hawa di Surga', 'Allah menempatkan Nabi Adam dan Hawa di surga dengan kenikmatan yang melimpah. Mereka hanya dilarang mendekati satu pohon.', 'https://storage.smarthijrah.com/kisah/adam/adam_episode2.pdf', 'https://storage.smarthijrah.com/kisah/adam/adam_cover2.jpg', 2, NOW()),
(1, 'Kisah Turun ke Bumi', 'Setelah terbuai bujukan iblis dan memakan buah khuldi, Nabi Adam dan Hawa diturunkan ke bumi untuk menjalani kehidupan sebagai khalifah.', 'https://storage.smarthijrah.com/kisah/adam/adam_episode3.pdf', 'https://storage.smarthijrah.com/kisah/adam/adam_cover3.jpg', 3, NOW());

-- Nabi Nuh (kisah_nabi_id = 3)
INSERT INTO kisah_nabi_episode (kisah_nabi_id, title, description, doc_url, cover_url, "order", created_at) VALUES
(3, 'Dakwah Nabi Nuh AS', 'Nabi Nuh berdakwah selama 950 tahun kepada kaumnya yang menyembah berhala. Hanya sedikit yang beriman.', 'https://storage.smarthijrah.com/kisah/nuh/nuh_episode1.pdf', 'https://storage.smarthijrah.com/kisah/nuh/nuh_cover1.jpg', 1, NOW()),
(3, 'Membangun Kapal', 'Atas perintah Allah, Nabi Nuh membangun kapal besar di tengah daratan. Kaumnya mengejek, namun kapal terus dibangun.', 'https://storage.smarthijrah.com/kisah/nuh/nuh_episode2.pdf', 'https://storage.smarthijrah.com/kisah/nuh/nuh_cover2.jpg', 2, NOW()),
(3, 'Banjir Bandang', 'Air keluar dari bumi dan langit, menenggelamkan semua yang kafir. Kapal Nabi Nuh terapung membawa umat beriman dan sepasang hewan.', 'https://storage.smarthijrah.com/kisah/nuh/nuh_episode3.pdf', 'https://storage.smarthijrah.com/kisah/nuh/nuh_cover3.jpg', 3, NOW());

-- Nabi Ibrahim (kisah_nabi_id = 6)
INSERT INTO kisah_nabi_episode (kisah_nabi_id, title, description, doc_url, cover_url, "order", created_at) VALUES
(6, 'Masa Kecil Ibrahim', 'Nabi Ibrahim kecil sudah berpikir tentang keberadaan Tuhan. Beliau melihat bintang, bulan, dan matahari, lalu menyadari bahwa Tuhannya bukan benda-benda itu.', 'https://storage.smarthijrah.com/kisah/ibrahim/ibrahim_episode1.pdf', 'https://storage.smarthijrah.com/kisah/ibrahim/ibrahim_cover1.jpg', 1, NOW()),
(6, 'Menghancurkan Berhala', 'Ketika kaumnya pergi, Nabi Ibrahim menghancurkan berhala-berhala besar, hanya menyisakan yang terbesar sebagai "pelaku".', 'https://storage.smarthijrah.com/kisah/ibrahim/ibrahim_episode2.pdf', 'https://storage.smarthijrah.com/kisah/ibrahim/ibrahim_cover2.jpg', 2, NOW()),
(6, 'Dilemparkan ke Api', 'Akibat perbuatannya, Raja Namrud menjatuhkan hukuman membakar Nabi Ibrahim. Namun api menjadi dingin dan selamat.', 'https://storage.smarthijrah.com/kisah/ibrahim/ibrahim_episode3.pdf', 'https://storage.smarthijrah.com/kisah/ibrahim/ibrahim_cover3.jpg', 3, NOW()),
(6, 'Menyembelih Ismail', 'Nabi Ibrahim mendapat mimpi untuk menyembelih putranya, Ismail. Setelah berjuang melawan godaan iblis, keduanya tunduk pada perintah Allah.', 'https://storage.smarthijrah.com/kisah/ibrahim/ibrahim_episode4.pdf', 'https://storage.smarthijrah.com/kisah/ibrahim/ibrahim_cover4.jpg', 4, NOW()),
(6, 'Membangun Ka''bah', 'Bersama Ismail, Nabi Ibrahim membangun Ka''bah sebagai rumah ibadah pertama bagi umat manusia.', 'https://storage.smarthijrah.com/kisah/ibrahim/ibrahim_episode5.pdf', 'https://storage.smarthijrah.com/kisah/ibrahim/ibrahim_cover5.jpg', 5, NOW());

-- Nabi Yusuf (tambahan, kisah_nabi_id = 11 kita buat dulu)
INSERT INTO kisah_nabi (prophet_name, total_read_count, main_cover, description, created_at, updated_at) VALUES
('Yusuf', 54321, 'kisah_nabi/covers/yusuf.jpg', 'Nabi Yusuf AS memiliki wajah tampan dan mimpi tentang sebelas bintang, matahari, dan bulan yang bersujud kepadanya. Kisahnya penuh liku-liku.', NOW(), NOW());

INSERT INTO kisah_nabi_episode (kisah_nabi_id, title, description, doc_url, cover_url, "order", created_at) VALUES
(11, 'Mimpi Nabi Yusuf', 'Nabi Yusuf bermimpi melihat sebelas bintang, matahari, dan bulan bersujud kepadanya. Mimpi ini membuat saudara-saudaranya iri.', 'https://storage.smarthijrah.com/kisah/yusuf/yusuf_episode1.pdf', 'https://storage.smarthijrah.com/kisah/yusuf/yusuf_cover1.jpg', 1, NOW()),
(11, 'Dibuang ke Sumur', 'Saudara-saudara Yusuf yang iri membuangnya ke dalam sumur, lalu menjualnya sebagai budak kepada kafilah yang lewat.', 'https://storage.smarthijrah.com/kisah/yusuf/yusuf_episode2.pdf', 'https://storage.smarthijrah.com/kisah/yusuf/yusuf_cover2.jpg', 2, NOW()),
(11, 'Di Rumah Al-Aziz', 'Nabi Yusuf dibeli oleh Al-Aziz, bendahara kerajaan Mesir. Ia tumbuh menjadi pemuda tampan dan diberi ilmu oleh Allah.', 'https://storage.smarthijrah.com/kisah/yusuf/yusuf_episode3.pdf', 'https://storage.smarthijrah.com/kisah/yusuf/yusuf_cover3.jpg', 3, NOW()),
(11, 'Fitnah Zulaikha', 'Istri Al-Aziz, Zulaikha, mencoba merayu Nabi Yusuf. Ketika ditolak, ia memfitnah Yusuf. Yusuf akhirnya dipenjara.', 'https://storage.smarthijrah.com/kisah/yusuf/yusuf_episode4.pdf', 'https://storage.smarthijrah.com/kisah/yusuf/yusuf_cover4.jpg', 4, NOW()),
(11, 'Menjadi Menteri Mesir', 'Setelah keluar dari penjara karena menakwilkan mimpi raja, Nabi Yusuf diangkat menjadi bendahara negara yang mengurus distribusi makanan.', 'https://storage.smarthijrah.com/kisah/yusuf/yusuf_episode5.pdf', 'https://storage.smarthijrah.com/kisah/yusuf/yusuf_cover5.jpg', 5, NOW()),
(11, 'Bertemu Keluarga', 'Saudara-saudara Yusuf datang ke Mesir meminta makanan. Yusuf akhirnya membuka identitasnya dan memaafkan mereka.', 'https://storage.smarthijrah.com/kisah/yusuf/yusuf_episode6.pdf', 'https://storage.smarthijrah.com/kisah/yusuf/yusuf_cover6.jpg', 6, NOW());


-- ============================================
-- UPDATE total_read_count menjadi lebih realistis
-- ============================================
UPDATE kisah_nabi SET total_read_count = total_read_count + FLOOR(RANDOM() * 10000)::int;