def error_handler(error_type, channel_id, price="", dkpc=None):
    if error_type == "loginFailed":
        # re_login(channel_id)
        return "loginFailed", "مشکل لاگین دیجیکالا."

    if error_type == "PROMOTION_UNHANDLED_BUG":
        return "DK_Error", "خطای دیجی‌کالا: محصول در صفحه تخفیف هوشمند وجود ندارد"

    if error_type == 'v2_token_not_exist':
        return "v2_token_not_exist", "استفاده از تخفیف هوشمند و استراتژی باکس لحظه‌ای و پلکانی، نیازمند اتصال به پنل از طریق نام کاربری و رمز دو مرحله‌ای می‌باشد"

    if error_type == "DeActive":
        return "DeActive", ".این تنوع در دیجی کالا غیرفعال است"

    if error_type == "range_is_not_valid":
        return "range_is_not_valid", "بازه قیمت‌گذاری شما صحیح نیست (حداقل حاشیه سود از حداکثر حاشیه سود بیشتر است)"

    if error_type == "no_stock":
        return "no_stock", '.موجودی تنوع به پایان رسیده است'

    if error_type == "DK_Error":
        return "DK_Error", ".وجود خطا از سمت دیجی‌کالا! در صورت تکرار خطا با پشتیبانی تماس بگیرید"

    if "DK_Error:" in error_type and 'موجودی این تنوع به پایان رسیده است' in error_type:
        return "no_stock", '.موجودی تنوع به پایان رسیده است'

    if "DK_Error:" in error_type:
        digikala_error_text = error_type.split(":")[1]
        return "DK_Error", "خطای دیجی کالا : " + digikala_error_text


    if error_type == "Mobisha_Error":
        return "Mobisha_Error", ".خطا در ارتباط با ربات! لطفا با پشتیبانی تماس بگیرید"

    if error_type == "out_of_range":
        return "out_of_range", ".امکان قیمت‌گذاری ({price} ریال) در بازه‌ی حداقل و حداکثر قیمت شما وجود ندارد".format(
            price=price)

    if error_type == "roundness_out_of_range":
        return "roundness_out_of_range", "قیمت رند شده شما ({price} ریال) خارج از بازه قیمت گذاری می‌باشد.".format(
            price=price)

    if error_type == "no_change_price_promotion":
        return "no_change_price_promotion", ".تغییر قیمت در پروموشن برای این تنوع فعال نیست"
    
    if error_type == "reactivation_error":
        return "reactivation_error", " خطا در فعال سازی مجدد تنوع. لطفا به پنل دیجی کالا مراجعه نمایید"
    
    if "reactivation_error:" in error_type:
        error_text = error_type.split(":")[1]
        return "reactivation_error", "خطا در فعال سازی مجدد تنوع : " + error_text

    if error_type == "offer_price_is_none":
        return "offer_price_is_none", ".خطا در قیمت گذاری"

    if error_type == "increase_price_problem":
        return 'increase_price_problem', 'افزایش قیمت به صورت آزاد با مشکل مواجه شد.'

    if error_type == "cant_deactivate":
        return 'cant_deactivate', 'مشکل در غیرفعال کردن تنوع در دیجیکالا'