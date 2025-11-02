package com.finance.demo;

import java.io.*;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

public class TransactionRepository {
    private static final String CSV_FILE = "transactions.csv";

    public Transaction save(Transaction transaction) {
        List<Transaction> transactions = loadTransactions();
        if (transaction.getId() == null) {
            long maxId = transactions.stream().mapToLong(t -> t.getId() != null ? t.getId() : 0).max().orElse(0);
            transaction.setId(maxId + 1);
        }
        transactions.add(transaction);
        saveTransactions(transactions);
        return transaction;
    }

    public List<Transaction> findAll() {
        return loadTransactions();
    }

    private List<Transaction> loadTransactions() {
        List<Transaction> transactions = new ArrayList<>();
        File file = new File(CSV_FILE);
        if (!file.exists()) {
            return transactions;
        }
        try (BufferedReader br = new BufferedReader(new FileReader(file))) {
            String line;
            boolean firstLine = true;
            while ((line = br.readLine()) != null) {
                if (firstLine) {
                    firstLine = false;
                    continue; // Skip header
                }
                String[] parts = line.split(",");
                if (parts.length == 5) {
                    Transaction t = new Transaction();
                    t.setId(Long.parseLong(parts[0]));
                    t.setDate(LocalDate.parse(parts[1]));
                    t.setAmount(new BigDecimal(parts[2]));
                    t.setDescription(parts[3]);
                    t.setPaymentType(parts[4]);
                    transactions.add(t);
                }
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
        return transactions;
    }

    private void saveTransactions(List<Transaction> transactions) {
        try (PrintWriter pw = new PrintWriter(new FileWriter(CSV_FILE))) {
            pw.println("id,date,amount,description,paymentType");
            for (Transaction t : transactions) {
                pw.println(t.getId() + "," + t.getDate() + "," + t.getAmount() + "," + t.getDescription() + "," + t.getPaymentType());
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
