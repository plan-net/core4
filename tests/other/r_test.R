library(feather)


pkgs_needed = c("nycflights13")
pkgs_installed = rownames(installed.packages())

for(pkg in pkgs_needed){
  if(pkg %in% pkgs_installed == FALSE){
    install.packages(pkg)
    print(paste("Installed package ",pkg))
  }
}

library(nycflights13)

df = head(flights)

return(df)

