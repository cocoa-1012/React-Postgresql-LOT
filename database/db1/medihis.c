#include <stdio.h>
#include <stdlib.h>

int main() {
  int i;
  for (i = 1; i < 544; i ++) {
    printf("CALL add_medical_history(");
    printf("%d", i);
    printf(", '3 doses, Fully vaccinated', NULL);\n");
  }
  for (; i < 777; i ++) {
    printf("CALL add_medical_history(");
    printf("%d", i);
    printf(", '3 doses, Fully vaccinated', 'negative');\n");
  }
  for (; i < 831; i ++) {
    printf("CALL add_medical_history(");
    printf("%d", i);
    printf(", '3 doses, Fully vaccinated', 'positive');\n");
  }
  for (; i < 900; i ++) {
    printf("CALL add_medical_history(");
    printf("%d", i);
    printf(", '2 doses, Pfizer-BioNTech', NULL);\n");
  }
  for (; i < 945; i ++) {
    printf("CALL add_medical_history(");
    printf("%d", i);
    printf(", '2 doses, Sinovac', NULL);\n");
  }
  for (; i < 998; i ++) {
    printf("CALL add_medical_history(");
    printf("%d", i);
    printf(", NULL, 'positive');\n");
  }
  for (; i < 1001; i ++) {
    printf("CALL add_medical_history(");
    printf("%d", i);
    printf(", NULL, 'negative');\n");
  }

  return 0;
}
