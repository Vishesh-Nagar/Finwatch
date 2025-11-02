package com.finance.demo;

import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDate;

@Data
public class Transaction {
    private Long id;
    private LocalDate date;
    private BigDecimal amount;
    private String description;
    private String paymentType;
}
