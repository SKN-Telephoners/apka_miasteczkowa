import { isAxiosError, AxiosError } from 'axios';


type ApiErrorMessage = {
    message?: string;
}

const httpStatusMessages: { [key: number]: string } = {
    400: 'Nieprawidłowe żądanie. Sprawdź wysłane dane.',
    500: 'Błąd serwera. Spróbuj ponownie później.',
    // add more 
}
export const parseAxiosError = (error: unknown): string => {
    if(isAxiosError(error)){
        const axiosError = error as AxiosError<ApiErrorResponse>; // change if trows error TypeError: Cannot read properties of undefined "as"
        const status = axiosError.response?.status;
        const backendMessage = axiosError.response?.data?.message;
        if(backendMessage){
            return backendMessage
        }
        if(status && httpStatusMessages[status]){
            return(httpStatusMessages[status])
        }
        if(axiosError){
            return axiosError.message;
        }
    }
}