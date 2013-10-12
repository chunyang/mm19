#!/usr/bin/env python2

from enemypdf import EnemyPDF
import numpy as np

pdf = EnemyPDF();

pdf.scan_decrease(100, 100)
pdf.decrease(98, 98)
pdf.decrease(40, 40)
pdf.decrease(40, 40)
pdf.decrease(47, 12)
pdf.decrease(2, 70)
pdf.scan_decrease(70, 20)

for i in range(60):
    for j in range(6):
        pdf.decrease(*pdf.next_scan())
    pdf.spread_mass()

print pdf.next_scan()
print pdf.next_scan()
print pdf.next_scan()
print pdf.next_scan()

print pdf.next_hit()
print pdf.next_hit()
print pdf.next_hit()
print pdf.next_hit()

pdf.show()
