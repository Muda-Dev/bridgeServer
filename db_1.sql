SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+03:00";

CREATE TABLE `ChainBlock` (`id` int NOT NULL,`last_seen_block` bigint NOT NULL,`updated_on` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE `ReceivedTransaction` (
`id` int NOT NULL,
`source` varchar(60) NOT NULL,
`destination` varchar(60) NOT NULL,
`transaction_id` varchar(80) NOT NULL,
`internal_transaction_id` varchar(50) NOT NULL,
`transaction_status` enum('PENDING','SUCCESS','REJECTED') NOT NULL,
`received_on` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
`payment_sent on` datetime NOT NULL,
`service_id` int NOT NULL,
`account_number` varchar(30) NOT NULL,
`received_obj` text NOT NULL,
`sent_object` text NOT NULL
);

CREATE TABLE `SentTransaction` (
`id` int NOT NULL,
`payment_id` varchar(255) DEFAULT NULL,
`transaction_id` varchar(64) NOT NULL,
`service_id` int NOT NULL,
`account_number` varchar(20) NOT NULL,
`status` enum('PENDING','SUCCESS','FAILED AND REFUNDED','NOT-REFUNDED')NOT NULL,
`thirdparty_transaction_id` varchar(50) NOT NULL,
`source` varchar(56) NOT NULL,
`destination` varchar(60) NOT NULL,
`submitted_at` datetime NOT NULL,
`succeeded_at` datetime DEFAULT NULL,
`request_obj` text,
`response_obj` varchar(255)
);

ALTER TABLE `ChainBlock` ADD PRIMARY KEY (`id`);

ALTER TABLE `ReceivedTransaction` ADD PRIMARY KEY (`id`), ADD UNIQUE KEY `transaction_id` (`transaction_id`);

ALTER TABLE `SentTransaction` ADD PRIMARY KEY (`id`),ADD UNIQUE KEY `transaction_id` (`transaction_id`),ADD UNIQUE KEY `payment_id` (`payment_id`);

ALTER TABLE `ChainBlock` MODIFY `id` int NOT NULL AUTO_INCREMENT;

ALTER TABLE `ReceivedTransaction` MODIFY `id` int NOT NULL AUTO_INCREMENT;

ALTER TABLE `SentTransaction` MODIFY `id` int NOT NULL AUTO_INCREMENT;
COMMIT;