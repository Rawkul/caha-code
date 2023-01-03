library(data.table)
library(magrittr)

source("../Common/errores.R")

dt <- fread("output/photometry.csv")

get_mag <- function(x, zmag = 25) -2.5 * log10(x) + zmag
get_err_mag <- function(x, err_x) abs(-2.5 / (x * log(10)) * err_x)
ZMAG <- 25

ferror <- function(f, x, err_x) {
  sapply(seq_along(x), function(i) {
    error_f(f, x[i], err_x[i])
  })
}

# Expresamos los errores adecuadamente
dt$general_err_flux <- error_signif(dt$general_err_flux)
dt$local_err_flux <- error_signif(dt$local_err_flux) 

# Expresar los flujos adecuadamente
dt$general_flux <- expresar_con_error(dt$general_flux, dt$general_err_flux)
dt$local_flux <- expresar_con_error(dt$local_flux, dt$local_err_flux)
  
# Calcular las magnitudes y expresarlas adecuadamente
dt$local_err_mag <- get_err_mag(dt$local_flux, dt$local_err_flux) %>%
  error_signif()
dt$general_err_mag <- get_err_mag(dt$general_flux, dt$general_err_flux) %>%
  error_signif()

dt$local_mag <- get_mag(dt$local_flux, ZMAG) %>% 
  expresar_con_error(dt$local_err_mag)
dt$general_mag <- get_mag(dt$general_flux, ZMAG) %>%
  expresar_con_error(dt$general_err_mag)

#---

target <- "V1301Cas"

dtv <- dt[filter == "V"]
dtb <- dt[filter == "B"]
dtr <- dt[filter == "R"]

par(mfrow = c(1,3))
plot(dtb$aperture, dtb$local_mag, pch = 20, cex = 0.5, xlab = "apertura", ylab = "m", main = "B")
plot(dtv$aperture, dtv$local_mag, pch = 20, cex = 0.5, xlab = "apertura", ylab = "m", main = "V")
plot(dtr$aperture, dtr$local_mag, pch = 20, cex = 0.5, xlab = "apertura", ylab = "m", main = "R")

dev.off()

# 10 is good enough
RADIUS <- 10

dt <- dt[aperture == RADIUS]

coords <- fread("data/auxiliar/objects-coords2.csv") %>%
  subset(select = c(object, B, eB, V, eV, R, eR))


# CALIBRACIÓN -------------------------------------------------------------
# Solo estrellas de comparación y añadimos sus magnitudes estándares según filtro
# y estrella
filters <- c("B", "V", "R")
stds <- c("UCAC3296-11655", "UCAC3296-11711", "CGCS68")
for (f in filters){
  for (s in stds){
    dt[filter == f & object == s,  `:=` (std_mag = coords[object == s][[f]],
                                         err_std_mag = coords[object == s][[paste0("e",f)]])][]
  }
}

# No hacemos calibración por masa de aire, si no por diferencia con las
# estrellas estándar

for (f in unique(dt$filename)) {
  
  if (f == "R") { # La estrella satura!
    aux <- dt[filename == f & object != target & object != "UCAC3296-11655"]
  } else {
    aux <- dt[filename == f & object != target]
  }
  
  std <- mean(aux$std_mag, na.rm = TRUE)
  std_err <- (sqrt(sum(aux$err_std_mag^2, na.rm = TRUE)) / nrow(aux)) %>% error_signif()
  
  l_err <- (sqrt(sum(aux$local_err_mag^2, na.rm = TRUE)) / nrow(aux)) %>% error_signif()
  l_ins <- mean(aux$local_mag, na.rm = TRUE) %>% expresar_con_error(l_err)
  
  g_err <- (sqrt(sum(aux$general_err_mag^2, na.rm = TRUE)) / nrow(aux)) %>% error_signif()
  g_ins <- mean(aux$general_mag, na.rm = TRUE) %>% expresar_con_error(g_err)
  
  
  dt[filename == f & object == target, `:=` (local_calc_mag = local_mag - l_ins + std,
                                             general_calc_mag = general_mag - g_ins + std,
                                             local_calc_err = local_err_mag + l_err + std_err,
                                             general_calc_err = local_err_mag + g_err + std_err)][]
  
}

dt <- dt[object == target]
dt$general_calc_err <- error_signif(dt$general_calc_err)
dt$local_calc_err <- error_signif(dt$local_calc_err)

dt$local_calc_mag <- expresar_con_error(dt$local_calc_mag, dt$local_calc_err)
dt$general_calc_mag <- expresar_con_error(dt$general_calc_mag, dt$general_calc_err)

mag <- list()
for (f in filters){
  aux <- copy(dt)[filter == f]
  
  aux$general_calc_err <- (0.5 * sqrt(aux$general_calc_err^2 + aux$local_calc_err^2)) %>%
    error_signif()
  aux$general_calc_mag <- (0.5 * (aux$general_calc_mag + aux$local_calc_mag)) %>%
    expresar_con_error(aux$general_calc_err)
  
  aux %>%
    setnames("general_calc_mag", f) %>%
    setnames("general_calc_err", paste0("e", f)) %>%
    setnames("date_end", "date")
  
  aux$time <- difftime(aux$date, min(aux$date), unit = "hours")
  
  aux <- subset(aux, select = c("filename", "date", "time", f, paste0("e", f), "exp_time"))
  
  # fwrite(aux, paste0("output/data/", f, ".csv"))
  fwrite(aux, paste0("output/data/", f, ".txt"), sep = " ")
  mag[[f]] <- aux
}

# TRANSFORM TO PHASE FORM

# Known period computed with period04:
P <- 5.4108 # hours

for (f in filters) {
  
  time <- mag[[f]]$time %>% as.numeric()
  time <- difftime(time, min(time), units = "hours") %>% as.numeric()
  
  for (i in seq_along(time)) {
    while (time[i] > P) {
      time[i] <- time[i] - P
    }
  }
  
  mag[[f]]$phase <- time / P - 0.5
  
  fwrite(mag[[f]], paste0("output/data/", f, ".csv"))
}
