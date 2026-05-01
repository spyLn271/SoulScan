use rusted_soul_dex::math::orca::clmm::{calculate_swap as calculate_swap_orca_clmm,
                                         get_lower_tick, get_upper_tick, get_amount_x,
                                         get_amount_y, tick_index_from_sqrt_price,
                                         sqrt_price_from_tick_index};
use rusted_soul_dex::math::raydium::amm::calculate_swap as calculate_swap_raydium_amm;

mod test_get_amount_x {
    use super::*;

    #[test]
    fn test_get_amount_x_test_0() {
        let sqrt_price0: u128 = 6549547715759401984;
        let sqrt_price1: u128 = 6550816156908514304;
        let liquidity: u128 = 605936807978762;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 330453729503;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_1() {
        let sqrt_price0: u128 = 39464783119120990208;
        let sqrt_price1: u128 = 39468380275379822592;
        let liquidity: u128 = 22619809754383;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 963626977;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_2() {
        let sqrt_price0: u128 = 1212844325845329482;
        let sqrt_price1: u128 = 1213275780100398080;
        let liquidity: u128 = 99050608057381;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 535731318893;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_3() {
        let sqrt_price0: u128 = 3457991179591266088;
        let sqrt_price1: u128 = 3469017564931659264;
        let liquidity: u128 = 6341221591114;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 107521530561;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_4() {
        let sqrt_price0: u128 = 550180929617695006761;
        let sqrt_price1: u128 = 550274975233931608064;
        let liquidity: u128 = 874088775688;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 5008740;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_5() {
        let sqrt_price0: u128 = 19766629503881962173;
        let sqrt_price1: u128 = 19767406098889322496;
        let liquidity: u128 = 21828117597909978;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 800291667207;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_6() {
        let sqrt_price0: u128 = 18446689868105869098;
        let sqrt_price1: u128 = 18446744073709551616;
        let liquidity: u128 = 24017826787399880;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 70576391182;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_7() {
        let sqrt_price0: u128 = 3061180542242421914;
        let sqrt_price1: u128 = 3061722530219793920;
        let liquidity: u128 = 115607959380355;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 123322504675;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_8() {
        let sqrt_price0: u128 = 219433924253101287;
        let sqrt_price1: u128 = 219601534794565536;
        let liquidity: u128 = 9931270627534;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 637216080877;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_9() {
        let sqrt_price0: u128 = 18448192998169328198;
        let sqrt_price1: u128 = 18448588748116922368;
        let liquidity: u128 = 15757399918968584;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 337993355560;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_10() {
        let sqrt_price0: u128 = 12043586314010063878;
        let sqrt_price1: u128 = 12052946592298522624;
        let liquidity: u128 = 31804148917860;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 37830597444;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_11() {
        let sqrt_price0: u128 = 133330402433652493777;
        let sqrt_price1: u128 = 133431594869585477632;
        let liquidity: u128 = 381962157397464;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 40077465011;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_12() {
        let sqrt_price0: u128 = 219817470516944561;
        let sqrt_price1: u128 = 219898182226379200;
        let liquidity: u128 = 1340381049657;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 41285799756;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_13() {
        let sqrt_price0: u128 = 16460928798828354736;
        let sqrt_price1: u128 = 16460993906453395456;
        let liquidity: u128 = 71551241868802066;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 317145359811;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_14() {
        let sqrt_price0: u128 = 17019653685085254167;
        let sqrt_price1: u128 = 17020047375749005312;
        let liquidity: u128 = 57754290757424;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 1447930144;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_15() {
        let sqrt_price0: u128 = 17101652679267006869;
        let sqrt_price1: u128 = 17101935883997196288;
        let liquidity: u128 = 11910322409684166;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 212745502274;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_16() {
        let sqrt_price0: u128 = 257165948088673153491;
        let sqrt_price1: u128 = 257213410979615670272;
        let liquidity: u128 = 534144246188;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 7070097;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_17() {
        let sqrt_price0: u128 = 6548526138012656305;
        let sqrt_price1: u128 = 6549833657298453504;
        let liquidity: u128 = 13051498504875;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 7339295399;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_18() {
        let sqrt_price0: u128 = 18447392657339170449;
        let sqrt_price1: u128 = 18447666387855958016;
        let liquidity: u128 = 24228678098245686;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 359497795625;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_19() {
        let sqrt_price0: u128 = 603272967711391461;
        let sqrt_price1: u128 = 603299749074910976;
        let liquidity: u128 = 1947569060880984;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 2643615342726;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_20() {
        let sqrt_price0: u128 = 6553120178631559168;
        let sqrt_price1: u128 = 6553764540098886656;
        let liquidity: u128 = 3631296816874;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 1005013895;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_21() {
        let sqrt_price0: u128 = 19147082635494154493;
        let sqrt_price1: u128 = 19147765352994283520;
        let liquidity: u128 = 257776075226777;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 8854879517;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_22() {
        let sqrt_price0: u128 = 52426120006993035262;
        let sqrt_price1: u128 = 52467063872978370560;
        let liquidity: u128 = 255033149849;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 70027839;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_23() {
        let sqrt_price0: u128 = 618603403299336250;
        let sqrt_price1: u128 = 618849987700050560;
        let liquidity: u128 = 245562770636;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 2917763953;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_24() {
        let sqrt_price0: u128 = 434573508383821093492;
        let sqrt_price1: u128 = 435950956741881495552;
        let liquidity: u128 = 435860378834504;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 58457677481;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_25() {
        let sqrt_price0: u128 = 18456469810742258782;
        let sqrt_price1: u128 = 18456892066001010688;
        let liquidity: u128 = 1023560174073920;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 23404585806;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_26() {
        let sqrt_price0: u128 = 6548833003078631533;
        let sqrt_price1: u128 = 6549833657298453504;
        let liquidity: u128 = 6791305619042;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 2922556002;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_27() {
        let sqrt_price0: u128 = 4062534991527260856;
        let sqrt_price1: u128 = 4062560884105892352;
        let liquidity: u128 = 9956967575063;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 288154311;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_28() {
        let sqrt_price0: u128 = 6545682955533397873;
        let sqrt_price1: u128 = 6550816156908514304;
        let liquidity: u128 = 21236570194026;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 46896671995;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_29() {
        let sqrt_price0: u128 = 18447074556370999907;
        let sqrt_price1: u128 = 18447666387855958016;
        let liquidity: u128 = 280468141184388;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 8997718153;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_30() {
        let sqrt_price0: u128 = 195902195886329548963;
        let sqrt_price1: u128 = 196835727405255393280;
        let liquidity: u128 = 237622246039238;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 106118858856;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_31() {
        let sqrt_price0: u128 = 6543369053712413671;
        let sqrt_price1: u128 = 6548523887035807744;
        let liquidity: u128 = 16881942792935;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 37463810012;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_32() {
        let sqrt_price0: u128 = 15626782727293835310;
        let sqrt_price1: u128 = 15626937319596955648;
        let liquidity: u128 = 3403527006347324;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 39745992554;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_33() {
        let sqrt_price0: u128 = 6546755240767077212;
        let sqrt_price1: u128 = 6547214378687926272;
        let liquidity: u128 = 2810437612756;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 555333878;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_34() {
        let sqrt_price0: u128 = 18453918773248178302;
        let sqrt_price1: u128 = 18454123878217465856;
        let liquidity: u128 = 36667675712666;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 407377698;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_35() {
        let sqrt_price0: u128 = 18468947633520724612;
        let sqrt_price1: u128 = 18469815767040602112;
        let liquidity: u128 = 2225019686708;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 104456481;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_36() {
        let sqrt_price0: u128 = 35069652309965234620;
        let sqrt_price1: u128 = 35096651307914342400;
        let liquidity: u128 = 1004582439302;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 406495562;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_37() {
        let sqrt_price0: u128 = 1071399398973729280235;
        let sqrt_price1: u128 = 1074794366720922353664;
        let liquidity: u128 = 103509434492472;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 5629353627;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_38() {
        let sqrt_price0: u128 = 1014984689916747566766;
        let sqrt_price1: u128 = 1021458901862740000768;
        let liquidity: u128 = 35790497773912;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 4122816304;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_39() {
        let sqrt_price0: u128 = 46361986214820773308;
        let sqrt_price1: u128 = 46378768775262035968;
        let liquidity: u128 = 3407338075532;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 490582350;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_40() {
        let sqrt_price0: u128 = 290398006802788377509;
        let sqrt_price1: u128 = 291328036695089315840;
        let liquidity: u128 = 3582193955739;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 726423379;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_41() {
        let sqrt_price0: u128 = 18463109050607017990;
        let sqrt_price1: u128 = 18463352785753513984;
        let liquidity: u128 = 205195506032121;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 2706389647;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_42() {
        let sqrt_price0: u128 = 277278011707260867;
        let sqrt_price1: u128 = 278161777933624896;
        let liquidity: u128 = 47891238231055;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 10122791794783;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_43() {
        let sqrt_price0: u128 = 22779465895519628803;
        let sqrt_price1: u128 = 22787845806202224640;
        let liquidity: u128 = 7501561530715;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 2233901289;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_44() {
        let sqrt_price0: u128 = 46040134853220702081;
        let sqrt_price1: u128 = 46186705295217016832;
        let liquidity: u128 = 29807348870305;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 37899711187;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_45() {
        let sqrt_price0: u128 = 691893968043721339518;
        let sqrt_price1: u128 = 692152729770434756608;
        let liquidity: u128 = 879462913268057;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 8765885884;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_46() {
        let sqrt_price0: u128 = 39360229755855504522;
        let sqrt_price1: u128 = 39486144154897711104;
        let liquidity: u128 = 2640704748570;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 3946504609;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_47() {
        let sqrt_price0: u128 = 39010158487911511320;
        let sqrt_price1: u128 = 39013214884994555904;
        let liquidity: u128 = 396192591425;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 14677307;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_48() {
        let sqrt_price0: u128 = 18446691441647151233;
        let sqrt_price1: u128 = 18446744073709551616;
        let liquidity: u128 = 2590596399535;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 7391484;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_49() {
        let sqrt_price0: u128 = 6549832458028776622;
        let sqrt_price1: u128 = 6550161140794435584;
        let liquidity: u128 = 698496791573;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 98714032;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_50() {
        let sqrt_price0: u128 = 17555635592413337273;
        let sqrt_price1: u128 = 17555904933687132160;
        let liquidity: u128 = 182779856635700;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 2946532167;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_51() {
        let sqrt_price0: u128 = 99638729697011933683;
        let sqrt_price1: u128 = 99673867628591792128;
        let liquidity: u128 = 163468336799;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 10668910;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_52() {
        let sqrt_price0: u128 = 18444799283409184578;
        let sqrt_price1: u128 = 18444899583751176192;
        let liquidity: u128 = 14386065669978059;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 78237316501;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_53() {
        let sqrt_price0: u128 = 112925671411751593;
        let sqrt_price1: u128 = 113647054646477312;
        let liquidity: u128 = 50473322851061;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 52335550678131;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_54() {
        let sqrt_price0: u128 = 7621379176857192718;
        let sqrt_price1: u128 = 7624235529176949760;
        let liquidity: u128 = 1471658669579;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 1334469700;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_55() {
        let sqrt_price0: u128 = 19154004500213056847;
        let sqrt_price1: u128 = 19154467908624453632;
        let liquidity: u128 = 256170267908077;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 5968740257;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_56() {
        let sqrt_price0: u128 = 429330081074343243;
        let sqrt_price1: u128 = 429654389814522688;
        let liquidity: u128 = 11706311051110;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 379653898210;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_57() {
        let sqrt_price0: u128 = 6366171485436555828;
        let sqrt_price1: u128 = 6371220394323397632;
        let liquidity: u128 = 9401483787731;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 21588014239;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_58() {
        let sqrt_price0: u128 = 18373362723983727830;
        let sqrt_price1: u128 = 18374026781617176576;
        let liquidity: u128 = 25916032479257120;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 940374875749;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_59() {
        let sqrt_price0: u128 = 18424559564897801939;
        let sqrt_price1: u128 = 18424622362569381888;
        let liquidity: u128 = 136887040180;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 467121;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_60() {
        let sqrt_price0: u128 = 48397534650602061215;
        let sqrt_price1: u128 = 48401928121926778880;
        let liquidity: u128 = 438176358787;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 15159698;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_61() {
        let sqrt_price0: u128 = 18473292303821105897;
        let sqrt_price1: u128 = 18473509914892165120;
        let liquidity: u128 = 347580423026;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 4088483;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_62() {
        let sqrt_price0: u128 = 1748823868077192790;
        let sqrt_price1: u128 = 1748845186342037760;
        let liquidity: u128 = 14842641341;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 1908469;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_63() {
        let sqrt_price0: u128 = 838359073321225199;
        let sqrt_price1: u128 = 841004962469682816;
        let liquidity: u128 = 494007582903370;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 34197657276009;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_64() {
        let sqrt_price0: u128 = 9557899667869391666;
        let sqrt_price1: u128 = 9565096768278011904;
        let liquidity: u128 = 944664995967;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 1371839400;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_65() {
        let sqrt_price0: u128 = 11400856924034713680;
        let sqrt_price1: u128 = 11402834135051294720;
        let liquidity: u128 = 1229306754494;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 344891673;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_66() {
        let sqrt_price0: u128 = 22495403799920661102;
        let sqrt_price1: u128 = 22495785039978283008;
        let liquidity: u128 = 342040089139939;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 4753355687;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_67() {
        let sqrt_price0: u128 = 45360650821130652707;
        let sqrt_price1: u128 = 45505933996253200384;
        let liquidity: u128 = 177720136529;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 230740789;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_68() {
        let sqrt_price0: u128 = 17215284876991313615;
        let sqrt_price1: u128 = 17216037018471129088;
        let liquidity: u128 = 269656981523519;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 12623608871;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_69() {
        let sqrt_price0: u128 = 66379391972875913304;
        let sqrt_price1: u128 = 66591284040703852544;
        let liquidity: u128 = 67210941052587;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 59432464372;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_70() {
        let sqrt_price0: u128 = 549616835165306828750;
        let sqrt_price1: u128 = 549834953286720749568;
        let liquidity: u128 = 23700681479;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 315558;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_71() {
        let sqrt_price0: u128 = 905811006607044642;
        let sqrt_price1: u128 = 906502520697171072;
        let liquidity: u128 = 5260728848027;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 81725966290;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_72() {
        let sqrt_price0: u128 = 6549124140214213451;
        let sqrt_price1: u128 = 6551471238524205056;
        let liquidity: u128 = 1338820989264;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 1350987883;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_73() {
        let sqrt_price0: u128 = 3649190444930693638;
        let sqrt_price1: u128 = 3650517292568695808;
        let liquidity: u128 = 3788932099680;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 6961561458;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_74() {
        let sqrt_price0: u128 = 17961481663694595299;
        let sqrt_price1: u128 = 17961655116854734848;
        let liquidity: u128 = 3434316013574173;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 34060708817;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_75() {
        let sqrt_price0: u128 = 2628547313352086884168;
        let sqrt_price1: u128 = 2636848580241801084928;
        let liquidity: u128 = 394626906599756;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 8718661216;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_76() {
        let sqrt_price0: u128 = 18453868613710027215;
        let sqrt_price1: u128 = 18454123878217465856;
        let liquidity: u128 = 16536995200;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 228657;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_77() {
        let sqrt_price0: u128 = 2628177332503444277;
        let sqrt_price1: u128 = 2636586664421109248;
        let liquidity: u128 = 520199772207;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 11645406645;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_78() {
        let sqrt_price0: u128 = 15853017520740943811;
        let sqrt_price1: u128 = 15853581809080356864;
        let liquidity: u128 = 1333494257680696;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 55229690652;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_79() {
        let sqrt_price0: u128 = 10212561437246484184;
        let sqrt_price1: u128 = 10216636540418570240;
        let liquidity: u128 = 4005068997299;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 2885530755;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_80() {
        let sqrt_price0: u128 = 46367480486912089909;
        let sqrt_price1: u128 = 46385725764495810560;
        let liquidity: u128 = 782504529868;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 122450116;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_81() {
        let sqrt_price0: u128 = 17755493265088520669;
        let sqrt_price1: u128 = 17756289466792615936;
        let liquidity: u128 = 1005869282561258;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 46859690165;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_82() {
        let sqrt_price0: u128 = 120843441711487542474;
        let sqrt_price1: u128 = 121619045717039644672;
        let liquidity: u128 = 78111748816413;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 76041635619;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_83() {
        let sqrt_price0: u128 = 25278077807508777305;
        let sqrt_price1: u128 = 25280216302050861056;
        let liquidity: u128 = 186987454880;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 11542915;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_84() {
        let sqrt_price0: u128 = 16361092895292661581;
        let sqrt_price1: u128 = 16361710492554143744;
        let liquidity: u128 = 5220700751140621;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 222184045464;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_85() {
        let sqrt_price0: u128 = 9781078943792311672;
        let sqrt_price1: u128 = 9843578216488419328;
        let liquidity: u128 = 3205810306833;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 38387757810;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_86() {
        let sqrt_price0: u128 = 59353572312029235747;
        let sqrt_price1: u128 = 59375366403381805056;
        let liquidity: u128 = 3856988136337;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 440000962;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_87() {
        let sqrt_price0: u128 = 26929517429876388282;
        let sqrt_price1: u128 = 26950960201201414144;
        let liquidity: u128 = 1530682652856;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 834224582;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_88() {
        let sqrt_price0: u128 = 18438263664155214987;
        let sqrt_price1: u128 = 18438445321166452736;
        let liquidity: u128 = 76191378181198;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 750988688;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_89() {
        let sqrt_price0: u128 = 18449470397529928157;
        let sqrt_price1: u128 = 18450433606991732736;
        let liquidity: u128 = 68453367993172;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 3573096967;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_90() {
        let sqrt_price0: u128 = 17131263725946502648;
        let sqrt_price1: u128 = 17137885886174756864;
        let liquidity: u128 = 17031230796883;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 7086287917;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_91() {
        let sqrt_price0: u128 = 57907513548854619733;
        let sqrt_price1: u128 = 58278332309661007872;
        let liquidity: u128 = 7032989104733;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 14255397520;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_92() {
        let sqrt_price0: u128 = 2199988026108752035;
        let sqrt_price1: u128 = 2207021882716549120;
        let liquidity: u128 = 1920133387027;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 51311850335;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_93() {
        let sqrt_price0: u128 = 2948393577371327060;
        let sqrt_price1: u128 = 2957751653947252736;
        let liquidity: u128 = 1295712650929;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 25648847410;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_94() {
        let sqrt_price0: u128 = 655594490157554069;
        let sqrt_price1: u128 = 655835499672833408;
        let liquidity: u128 = 98274788232290;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 1016168697516;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_95() {
        let sqrt_price0: u128 = 1516319742892191414;
        let sqrt_price1: u128 = 1516890917590342912;
        let liquidity: u128 = 16019419126535;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 73382128898;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_96() {
        let sqrt_price0: u128 = 3470755481804934092;
        let sqrt_price1: u128 = 3487451242454726144;
        let liquidity: u128 = 39045505369464;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 993493015101;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_97() {
        let sqrt_price0: u128 = 38384513664787349978;
        let sqrt_price1: u128 = 38507425175389700096;
        let liquidity: u128 = 1064320282609;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 1632616173;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_98() {
        let sqrt_price0: u128 = 9146987716393772849;
        let sqrt_price1: u128 = 9176288266633526272;
        let liquidity: u128 = 471460877699;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 3035959788;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_99() {
        let sqrt_price0: u128 = 18640027337878358888;
        let sqrt_price1: u128 = 18640513543194677248;
        let liquidity: u128 = 1180961755602840;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 30483921981;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_100() {
        let sqrt_price0: u128 = 17362094953421462923;
        let sqrt_price1: u128 = 17362121565192491008;
        let liquidity: u128 = 1623027012360868;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 2643104467;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_101() {
        let sqrt_price0: u128 = 25089316183865860096;
        let sqrt_price1: u128 = 25209534231525126144;
        let liquidity: u128 = 2981399612286;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 10453360728;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_102() {
        let sqrt_price0: u128 = 18446111037002145552;
        let sqrt_price1: u128 = 18446744073709551616;
        let liquidity: u128 = 317910113268422;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 10910092157;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_103() {
        let sqrt_price0: u128 = 18011655170469663575;
        let sqrt_price1: u128 = 18025529108130107392;
        let liquidity: u128 = 1235903717743;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 974232143;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_104() {
        let sqrt_price0: u128 = 16204813545401416;
        let sqrt_price1: u128 = 16217566108615620;
        let liquidity: u128 = 62592790226336;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 56028862296431;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_105() {
        let sqrt_price0: u128 = 18437236087570197405;
        let sqrt_price1: u128 = 18437523468038801408;
        let liquidity: u128 = 515101301610780;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 8032878819;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_106() {
        let sqrt_price0: u128 = 177635871001459229540;
        let sqrt_price1: u128 = 177776048204628262912;
        let liquidity: u128 = 274556102176;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 22481448;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_107() {
        let sqrt_price0: u128 = 36820465264522248136;
        let sqrt_price1: u128 = 36938455551937093632;
        let liquidity: u128 = 1052858943878;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 1684876865;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_108() {
        let sqrt_price0: u128 = 133604018275432097;
        let sqrt_price1: u128 = 134026747335230560;
        let liquidity: u128 = 14889176993699;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 6483977821525;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_109() {
        let sqrt_price0: u128 = 46017696168523912;
        let sqrt_price1: u128 = 46311602260023392;
        let liquidity: u128 = 235515704401496;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 599147156293642;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_110() {
        let sqrt_price0: u128 = 18409329122351124577;
        let sqrt_price1: u128 = 18423701200537831424;
        let liquidity: u128 = 58077969904;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 45397911;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_111() {
        let sqrt_price0: u128 = 226729791226073561;
        let sqrt_price1: u128 = 227446021879295872;
        let liquidity: u128 = 22535461501132;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 5773672549512;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_112() {
        let sqrt_price0: u128 = 6543346569538326201;
        let sqrt_price1: u128 = 6564258431551793152;
        let liquidity: u128 = 1120753175599;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 10065533789;

        assert_eq!(amount_x, result_should_be)
    }


    #[test]
    fn test_get_amount_x_test_113() {
        let sqrt_price0: u128 = 40155217713283358;
        let sqrt_price1: u128 = 40283803524082848;
        let liquidity: u128 = 59766380645963;

        let amount_x = get_amount_x(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 87638971582120;

        assert_eq!(amount_x, result_should_be)
    }
}

mod test_get_amount_y {
    use super::*;

    #[test]
    fn test_get_amount_y_test_0() {
        let sqrt_price0: u128 = 6549547715759401984;
        let sqrt_price1: u128 = 6550816156908514304;
        let liquidity: u128 = 605936807978762;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 41665628250;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_1() {
        let sqrt_price0: u128 = 39464783119120990208;
        let sqrt_price1: u128 = 39468380275379822592;
        let liquidity: u128 = 22619809754383;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 4410913378;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_2() {
        let sqrt_price0: u128 = 1212844325845329482;
        let sqrt_price1: u128 = 1213275780100398080;
        let liquidity: u128 = 99050608057381;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 2316712702;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_3() {
        let sqrt_price0: u128 = 3457991179591266088;
        let sqrt_price1: u128 = 3469017564931659264;
        let liquidity: u128 = 6341221591114;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 3790411603;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_4() {
        let sqrt_price0: u128 = 550180929617695006761;
        let sqrt_price1: u128 = 550274975233931608064;
        let liquidity: u128 = 874088775688;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 4456299563;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_5() {
        let sqrt_price0: u128 = 19766629503881962173;
        let sqrt_price1: u128 = 19767406098889322496;
        let liquidity: u128 = 21828117597909978;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 918948464773;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_6() {
        let sqrt_price0: u128 = 18446689868105869098;
        let sqrt_price1: u128 = 18446744073709551616;
        let liquidity: u128 = 24017826787399880;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 70576183794;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_7() {
        let sqrt_price0: u128 = 3061180542242421914;
        let sqrt_price1: u128 = 3061722530219793920;
        let liquidity: u128 = 115607959380355;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 3396703712;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_8() {
        let sqrt_price0: u128 = 219433924253101287;
        let sqrt_price1: u128 = 219601534794565536;
        let liquidity: u128 = 9931270627534;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 90237368;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_9() {
        let sqrt_price0: u128 = 18448192998169328198;
        let sqrt_price1: u128 = 18448588748116922368;
        let liquidity: u128 = 15757399918968584;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 338053705696;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_10() {
        let sqrt_price0: u128 = 12043586314010063878;
        let sqrt_price1: u128 = 12052946592298522624;
        let liquidity: u128 = 31804148917860;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 16138115399;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_11() {
        let sqrt_price0: u128 = 133330402433652493777;
        let sqrt_price1: u128 = 133431594869585477632;
        let liquidity: u128 = 381962157397464;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 2095311833178;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_12() {
        let sqrt_price0: u128 = 219817470516944561;
        let sqrt_price1: u128 = 219898182226379200;
        let liquidity: u128 = 1340381049657;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 5864690;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_13() {
        let sqrt_price0: u128 = 16460928798828354736;
        let sqrt_price1: u128 = 16460993906453395456;
        let liquidity: u128 = 71551241868802066;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 252539494675;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_14() {
        let sqrt_price0: u128 = 17019653685085254167;
        let sqrt_price1: u128 = 17020047375749005312;
        let liquidity: u128 = 57754290757424;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 1232592861;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_15() {
        let sqrt_price0: u128 = 17101652679267006869;
        let sqrt_price1: u128 = 17101935883997196288;
        let liquidity: u128 = 11910322409684166;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 182853929724;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_16() {
        let sqrt_price0: u128 = 257165948088673153491;
        let sqrt_price1: u128 = 257213410979615670272;
        let liquidity: u128 = 534144246188;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 1374336305;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_17() {
        let sqrt_price0: u128 = 6548526138012656305;
        let sqrt_price1: u128 = 6549833657298453504;
        let liquidity: u128 = 13051498504875;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 925100165;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_18() {
        let sqrt_price0: u128 = 18447392657339170449;
        let sqrt_price1: u128 = 18447666387855958016;
        let liquidity: u128 = 24228678098245686;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 359528410564;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_19() {
        let sqrt_price0: u128 = 603272967711391461;
        let sqrt_price1: u128 = 603299749074910976;
        let liquidity: u128 = 1947569060880984;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 2827520932;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_20() {
        let sqrt_price0: u128 = 6553120178631559168;
        let sqrt_price1: u128 = 6553764540098886656;
        let liquidity: u128 = 3631296816874;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 126844484;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_21() {
        let sqrt_price0: u128 = 19147082635494154493;
        let sqrt_price1: u128 = 19147765352994283520;
        let liquidity: u128 = 257776075226777;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 9540341480;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_22() {
        let sqrt_price0: u128 = 52426120006993035262;
        let sqrt_price1: u128 = 52467063872978370560;
        let liquidity: u128 = 255033149849;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 566064291;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_23() {
        let sqrt_price0: u128 = 618603403299336250;
        let sqrt_price1: u128 = 618849987700050560;
        let liquidity: u128 = 245562770636;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 3282527;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_24() {
        let sqrt_price0: u128 = 434573508383821093492;
        let sqrt_price1: u128 = 435950956741881495552;
        let liquidity: u128 = 435860378834504;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 32546402810717;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_25() {
        let sqrt_price0: u128 = 18456469810742258782;
        let sqrt_price1: u128 = 18456892066001010688;
        let liquidity: u128 = 1023560174073920;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 23429807689;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_26() {
        let sqrt_price0: u128 = 6548833003078631533;
        let sqrt_price1: u128 = 6549833657298453504;
        let liquidity: u128 = 6791305619042;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 368398271;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_27() {
        let sqrt_price0: u128 = 4062534991527260856;
        let sqrt_price1: u128 = 4062560884105892352;
        let liquidity: u128 = 9956967575063;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 13975992;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_28() {
        let sqrt_price0: u128 = 6545682955533397873;
        let sqrt_price1: u128 = 6550816156908514304;
        let liquidity: u128 = 21236570194026;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 5909530206;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_29() {
        let sqrt_price0: u128 = 18447074556370999907;
        let sqrt_price1: u128 = 18447666387855958016;
        let liquidity: u128 = 280468141184388;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 8998329234;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_30() {
        let sqrt_price0: u128 = 195902195886329548963;
        let sqrt_price1: u128 = 196835727405255393280;
        let liquidity: u128 = 237622246039238;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 12025312184589;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_31() {
        let sqrt_price0: u128 = 6543369053712413671;
        let sqrt_price1: u128 = 6548523887035807744;
        let liquidity: u128 = 16881942792935;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 4717558877;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_32() {
        let sqrt_price0: u128 = 15626782727293835310;
        let sqrt_price1: u128 = 15626937319596955648;
        let liquidity: u128 = 3403527006347324;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 28523140806;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_33() {
        let sqrt_price0: u128 = 6546755240767077212;
        let sqrt_price1: u128 = 6547214378687926272;
        let liquidity: u128 = 2810437612756;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 69951557;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_34() {
        let sqrt_price0: u128 = 18453918773248178302;
        let sqrt_price1: u128 = 18454123878217465856;
        let liquidity: u128 = 36667675712666;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 407699183;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_35() {
        let sqrt_price0: u128 = 18468947633520724612;
        let sqrt_price1: u128 = 18469815767040602112;
        let liquidity: u128 = 2225019686708;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 104713014;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_36() {
        let sqrt_price0: u128 = 35069652309965234620;
        let sqrt_price1: u128 = 35096651307914342400;
        let liquidity: u128 = 1004582439302;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 1470325555;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_37() {
        let sqrt_price0: u128 = 1071399398973729280235;
        let sqrt_price1: u128 = 1074794366720922353664;
        let liquidity: u128 = 103509434492472;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 19050038870164;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_38() {
        let sqrt_price0: u128 = 1014984689916747566766;
        let sqrt_price1: u128 = 1021458901862740000768;
        let liquidity: u128 = 35790497773912;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 12561309861240;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_39() {
        let sqrt_price0: u128 = 46361986214820773308;
        let sqrt_price1: u128 = 46378768775262035968;
        let liquidity: u128 = 3407338075532;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 3099943110;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_40() {
        let sqrt_price0: u128 = 290398006802788377509;
        let sqrt_price1: u128 = 291328036695089315840;
        let liquidity: u128 = 3582193955739;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 180603549631;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_41() {
        let sqrt_price0: u128 = 18463109050607017990;
        let sqrt_price1: u128 = 18463352785753513984;
        let liquidity: u128 = 205195506032121;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 2711229500;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_42() {
        let sqrt_price0: u128 = 277278011707260867;
        let sqrt_price1: u128 = 278161777933624896;
        let liquidity: u128 = 47891238231055;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 2294424355;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_43() {
        let sqrt_price0: u128 = 22779465895519628803;
        let sqrt_price1: u128 = 22787845806202224640;
        let liquidity: u128 = 7501561530715;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 3407778378;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_44() {
        let sqrt_price0: u128 = 46040134853220702081;
        let sqrt_price1: u128 = 46186705295217016832;
        let liquidity: u128 = 29807348870305;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 236837258716;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_45() {
        let sqrt_price0: u128 = 691893968043721339518;
        let sqrt_price1: u128 = 692152729770434756608;
        let liquidity: u128 = 879462913268057;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 12336667170549;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_46() {
        let sqrt_price0: u128 = 39360229755855504522;
        let sqrt_price1: u128 = 39486144154897711104;
        let liquidity: u128 = 2640704748570;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 18025010274;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_47() {
        let sqrt_price0: u128 = 39010158487911511320;
        let sqrt_price1: u128 = 39013214884994555904;
        let liquidity: u128 = 396192591425;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 65644206;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_48() {
        let sqrt_price0: u128 = 18446691441647151233;
        let sqrt_price1: u128 = 18446744073709551616;
        let liquidity: u128 = 2590596399535;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 7391463;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_49() {
        let sqrt_price0: u128 = 6549832458028776622;
        let sqrt_price1: u128 = 6550161140794435584;
        let liquidity: u128 = 698496791573;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 12445765;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_50() {
        let sqrt_price0: u128 = 17555635592413337273;
        let sqrt_price1: u128 = 17555904933687132160;
        let liquidity: u128 = 182779856635700;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 2668772289;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_51() {
        let sqrt_price0: u128 = 99638729697011933683;
        let sqrt_price1: u128 = 99673867628591792128;
        let liquidity: u128 = 163468336799;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 311379569;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_52() {
        let sqrt_price0: u128 = 18444799283409184578;
        let sqrt_price1: u128 = 18444899583751176192;
        let liquidity: u128 = 14386065669978059;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 78221246028;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_53() {
        let sqrt_price0: u128 = 112925671411751593;
        let sqrt_price1: u128 = 113647054646477312;
        let liquidity: u128 = 50473322851061;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 1973823063;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_54() {
        let sqrt_price0: u128 = 7621379176857192718;
        let sqrt_price1: u128 = 7624235529176949760;
        let liquidity: u128 = 1471658669579;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 227876292;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_55() {
        let sqrt_price0: u128 = 19154004500213056847;
        let sqrt_price1: u128 = 19154467908624453632;
        let liquidity: u128 = 256170267908077;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 6435360973;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_56() {
        let sqrt_price0: u128 = 429330081074343243;
        let sqrt_price1: u128 = 429654389814522688;
        let liquidity: u128 = 11706311051110;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 205806454;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_57() {
        let sqrt_price0: u128 = 6366171485436555828;
        let sqrt_price1: u128 = 6371220394323397632;
        let liquidity: u128 = 9401483787731;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 2573203967;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_58() {
        let sqrt_price0: u128 = 18373362723983727830;
        let sqrt_price1: u128 = 18374026781617176576;
        let liquidity: u128 = 25916032479257120;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 932941831240;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_59() {
        let sqrt_price0: u128 = 18424559564897801939;
        let sqrt_price1: u128 = 18424622362569381888;
        let liquidity: u128 = 136887040180;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 466000;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_60() {
        let sqrt_price0: u128 = 48397534650602061215;
        let sqrt_price1: u128 = 48401928121926778880;
        let liquidity: u128 = 438176358787;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 104360707;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_61() {
        let sqrt_price0: u128 = 18473292303821105897;
        let sqrt_price1: u128 = 18473509914892165120;
        let liquidity: u128 = 347580423026;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 4100308;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_62() {
        let sqrt_price0: u128 = 1748823868077192790;
        let sqrt_price1: u128 = 1748845186342037760;
        let liquidity: u128 = 14842641341;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 17153;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_63() {
        let sqrt_price0: u128 = 838359073321225199;
        let sqrt_price1: u128 = 841004962469682816;
        let liquidity: u128 = 494007582903370;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 70857453089;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_64() {
        let sqrt_price0: u128 = 9557899667869391666;
        let sqrt_price1: u128 = 9565096768278011904;
        let liquidity: u128 = 944664995967;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 368566333;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_65() {
        let sqrt_price0: u128 = 11400856924034713680;
        let sqrt_price1: u128 = 11402834135051294720;
        let liquidity: u128 = 1229306754494;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 131763028;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_66() {
        let sqrt_price0: u128 = 22495403799920661102;
        let sqrt_price1: u128 = 22495785039978283008;
        let liquidity: u128 = 342040089139939;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 7068964732;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_67() {
        let sqrt_price0: u128 = 45360650821130652707;
        let sqrt_price1: u128 = 45505933996253200384;
        let liquidity: u128 = 177720136529;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 1399691220;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_68() {
        let sqrt_price0: u128 = 17215284876991313615;
        let sqrt_price1: u128 = 17216037018471129088;
        let liquidity: u128 = 269656981523519;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 10994905134;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_69() {
        let sqrt_price0: u128 = 66379391972875913304;
        let sqrt_price1: u128 = 66591284040703852544;
        let liquidity: u128 = 67210941052587;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 772031379813;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_70() {
        let sqrt_price0: u128 = 549616835165306828750;
        let sqrt_price1: u128 = 549834953286720749568;
        let liquidity: u128 = 23700681479;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 280241765;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_71() {
        let sqrt_price0: u128 = 905811006607044642;
        let sqrt_price1: u128 = 906502520697171072;
        let liquidity: u128 = 5260728848027;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 197209226;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_72() {
        let sqrt_price0: u128 = 6549124140214213451;
        let sqrt_price1: u128 = 6551471238524205056;
        let liquidity: u128 = 1338820989264;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 170346835;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_73() {
        let sqrt_price0: u128 = 3649190444930693638;
        let sqrt_price1: u128 = 3650517292568695808;
        let liquidity: u128 = 3788932099680;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 272532409;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_74() {
        let sqrt_price0: u128 = 17961481663694595299;
        let sqrt_price1: u128 = 17961655116854734848;
        let liquidity: u128 = 3434316013574173;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 32292580364;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_75() {
        let sqrt_price0: u128 = 2628547313352086884168;
        let sqrt_price1: u128 = 2636848580241801084928;
        let liquidity: u128 = 394626906599756;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 177587072301595;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_76() {
        let sqrt_price0: u128 = 18453868613710027215;
        let sqrt_price1: u128 = 18454123878217465856;
        let liquidity: u128 = 16536995200;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 228837;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_77() {
        let sqrt_price0: u128 = 2628177332503444277;
        let sqrt_price1: u128 = 2636586664421109248;
        let liquidity: u128 = 520199772207;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 237143884;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_78() {
        let sqrt_price0: u128 = 15853017520740943811;
        let sqrt_price1: u128 = 15853581809080356864;
        let liquidity: u128 = 1333494257680696;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 40791765597;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_79() {
        let sqrt_price0: u128 = 10212561437246484184;
        let sqrt_price1: u128 = 10216636540418570240;
        let liquidity: u128 = 4005068997299;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 884766943;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_80() {
        let sqrt_price0: u128 = 46367480486912089909;
        let sqrt_price1: u128 = 46385725764495810560;
        let liquidity: u128 = 782504529868;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 773958390;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_81() {
        let sqrt_price0: u128 = 17755493265088520669;
        let sqrt_price1: u128 = 17756289466792615936;
        let liquidity: u128 = 1005869282561258;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 43415511901;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_82() {
        let sqrt_price0: u128 = 120843441711487542474;
        let sqrt_price1: u128 = 121619045717039644672;
        let liquidity: u128 = 78111748816413;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 3284253579960;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_83() {
        let sqrt_price0: u128 = 25278077807508777305;
        let sqrt_price1: u128 = 25280216302050861056;
        let liquidity: u128 = 186987454880;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 21677085;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_84() {
        let sqrt_price0: u128 = 16361092895292661581;
        let sqrt_price1: u128 = 16361710492554143744;
        let liquidity: u128 = 5220700751140621;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 174789137532;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_85() {
        let sqrt_price0: u128 = 9781078943792311672;
        let sqrt_price1: u128 = 9843578216488419328;
        let liquidity: u128 = 3205810306833;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 10861581413;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_86() {
        let sqrt_price0: u128 = 59353572312029235747;
        let sqrt_price1: u128 = 59375366403381805056;
        let liquidity: u128 = 3856988136337;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 4556877433;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_87() {
        let sqrt_price0: u128 = 26929517429876388282;
        let sqrt_price1: u128 = 26950960201201414144;
        let liquidity: u128 = 1530682652856;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 1779288418;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_88() {
        let sqrt_price0: u128 = 18438263664155214987;
        let sqrt_price1: u128 = 18438445321166452736;
        let liquidity: u128 = 76191378181198;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 750305744;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_89() {
        let sqrt_price0: u128 = 18449470397529928157;
        let sqrt_price1: u128 = 18450433606991732736;
        let liquidity: u128 = 68453367993172;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 3574339811;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_90() {
        let sqrt_price0: u128 = 17131263725946502648;
        let sqrt_price1: u128 = 17137885886174756864;
        let liquidity: u128 = 17031230796883;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 6114007912;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_91() {
        let sqrt_price0: u128 = 57907513548854619733;
        let sqrt_price1: u128 = 58278332309661007872;
        let liquidity: u128 = 7032989104733;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 141378028239;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_92() {
        let sqrt_price0: u128 = 2199988026108752035;
        let sqrt_price1: u128 = 2207021882716549120;
        let liquidity: u128 = 1920133387027;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 732158632;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_93() {
        let sqrt_price0: u128 = 2948393577371327060;
        let sqrt_price1: u128 = 2957751653947252736;
        let liquidity: u128 = 1295712650929;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 657318069;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_94() {
        let sqrt_price0: u128 = 655594490157554069;
        let sqrt_price1: u128 = 655835499672833408;
        let liquidity: u128 = 98274788232290;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 1283975046;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_95() {
        let sqrt_price0: u128 = 1516319742892191414;
        let sqrt_price1: u128 = 1516890917590342912;
        let liquidity: u128 = 16019419126535;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 496016361;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_96() {
        let sqrt_price0: u128 = 3470755481804934092;
        let sqrt_price1: u128 = 3487451242454726144;
        let liquidity: u128 = 39045505369464;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 35339266891;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_97() {
        let sqrt_price0: u128 = 38384513664787349978;
        let sqrt_price1: u128 = 38507425175389700096;
        let liquidity: u128 = 1064320282609;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 7091615364;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_98() {
        let sqrt_price0: u128 = 9146987716393772849;
        let sqrt_price1: u128 = 9176288266633526272;
        let liquidity: u128 = 471460877699;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 748861862;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_99() {
        let sqrt_price0: u128 = 18640027337878358888;
        let sqrt_price1: u128 = 18640513543194677248;
        let liquidity: u128 = 1180961755602840;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 31126895979;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_100() {
        let sqrt_price0: u128 = 17362094953421462923;
        let sqrt_price1: u128 = 17362121565192491008;
        let liquidity: u128 = 1623027012360868;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 2341422586;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_101() {
        let sqrt_price0: u128 = 25089316183865860096;
        let sqrt_price1: u128 = 25209534231525126144;
        let liquidity: u128 = 2981399612286;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 19429880918;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_102() {
        let sqrt_price0: u128 = 18446111037002145552;
        let sqrt_price1: u128 = 18446744073709551616;
        let liquidity: u128 = 317910113268422;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 10909717755;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_103() {
        let sqrt_price0: u128 = 18011655170469663575;
        let sqrt_price1: u128 = 18025529108130107392;
        let liquidity: u128 = 1235903717743;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 929532662;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_104() {
        let sqrt_price0: u128 = 16204813545401416;
        let sqrt_price1: u128 = 16217566108615620;
        let liquidity: u128 = 62592790226336;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 43271512;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_105() {
        let sqrt_price0: u128 = 18437236087570197405;
        let sqrt_price1: u128 = 18437523468038801408;
        let liquidity: u128 = 515101301610780;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 8024725276;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_106() {
        let sqrt_price0: u128 = 177635871001459229540;
        let sqrt_price1: u128 = 177776048204628262912;
        let liquidity: u128 = 274556102176;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 2086357698;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_107() {
        let sqrt_price0: u128 = 36820465264522248136;
        let sqrt_price1: u128 = 36938455551937093632;
        let liquidity: u128 = 1052858943878;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 6734366178;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_108() {
        let sqrt_price0: u128 = 133604018275432097;
        let sqrt_price1: u128 = 134026747335230560;
        let liquidity: u128 = 14889176993699;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 341203182;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_109() {
        let sqrt_price0: u128 = 46017696168523912;
        let sqrt_price1: u128 = 46311602260023392;
        let liquidity: u128 = 235515704401496;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 3752396622;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_110() {
        let sqrt_price0: u128 = 18409329122351124577;
        let sqrt_price1: u128 = 18423701200537831424;
        let liquidity: u128 = 58077969904;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 45249238;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_111() {
        let sqrt_price0: u128 = 226729791226073561;
        let sqrt_price1: u128 = 227446021879295872;
        let liquidity: u128 = 22535461501132;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 874983045;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_112() {
        let sqrt_price0: u128 = 6543346569538326201;
        let sqrt_price1: u128 = 6564258431551793152;
        let liquidity: u128 = 1120753175599;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 1270524254;

        assert_eq!(amount_y, result_should_be)
    }


    #[test]
    fn test_get_amount_y_test_113() {
        let sqrt_price0: u128 = 40155217713283358;
        let sqrt_price1: u128 = 40283803524082848;
        let liquidity: u128 = 59766380645963;

        let amount_y = get_amount_y(sqrt_price0, sqrt_price1, liquidity, false);
        let result_should_be: u128 = 416610567;

        assert_eq!(amount_y, result_should_be)
    }

}

mod test_tick {
    use super::*;

    #[test]
    fn test_upper_tick_0(){
        // [2560, 2624)
        let current_tick = 2560;
        let tick_spacing = 64;
        let upper_tick = get_upper_tick(current_tick, tick_spacing);
        assert_eq!(upper_tick, 2624)
    }

    #[test]
    fn test_upper_tick_1(){
        // [2560, 2624)
        let current_tick = 2584;
        let tick_spacing = 64;
        let upper_tick = get_upper_tick(current_tick, tick_spacing);
        assert_eq!(upper_tick, 2624)
    }

    #[test]
    fn test_upper_tick_2(){
        // [2624, 2688)
        let current_tick = 2624;
        let tick_spacing = 64;
        let upper_tick = get_upper_tick(current_tick, tick_spacing);
        assert_eq!(upper_tick, 2688)
    }

    #[test]
    fn test_upper_tick_3() {
        // [-6208, -6144)
        let current_tick = -6208;
        let tick_spacing = 64;
        let upper_tick = get_upper_tick(current_tick, tick_spacing);
        assert_eq!(upper_tick, -6144)
    }

    #[test]
    fn test_upper_tick_4() {
        // [-6208, -6144)
        let current_tick = -6186;
        let tick_spacing = 64;
        let upper_tick = get_upper_tick(current_tick, tick_spacing);
        assert_eq!(upper_tick, -6144)
    }

    #[test]
    fn test_upper_tick_5() {
        // [-6144, -6080)
        let current_tick = -6144;
        let tick_spacing = 64;
        let upper_tick = get_upper_tick(current_tick, tick_spacing);
        assert_eq!(upper_tick, -6080)
    }

    #[test]
    fn test_lower_tick_0(){
        // [2560, 2624)
        let current_tick = 2560;
        let tick_spacing = 64;
        let upper_tick = get_lower_tick(current_tick, tick_spacing);
        assert_eq!(upper_tick, 2560)
    }

    #[test]
    fn test_lower_tick_1(){
        // [2560, 2624)
        let current_tick = 2584;
        let tick_spacing = 64;
        let upper_tick = get_lower_tick(current_tick, tick_spacing);
        assert_eq!(upper_tick, 2560)
    }

    #[test]
    fn test_lower_tick_2(){
        // [2624, 2688)
        let current_tick = 2624;
        let tick_spacing = 64;
        let upper_tick = get_lower_tick(current_tick, tick_spacing);
        assert_eq!(upper_tick, 2624)
    }

    #[test]
    fn test_lower_tick_3(){
        // [-6208, -6208)
        let current_tick = -6208;
        let tick_spacing = 64;
        let upper_tick = get_lower_tick(current_tick, tick_spacing);
        assert_eq!(upper_tick, -6208)
    }

    #[test]
    fn test_lower_tick_4(){
        // [-6208, -6208)
        let current_tick = -6186;
        let tick_spacing = 64;
        let upper_tick = get_lower_tick(current_tick, tick_spacing);
        assert_eq!(upper_tick, -6208)
    }

    #[test]
    fn test_lower_tick_5(){
        // [-6208, -6144)
        let current_tick = -6208;
        let tick_spacing = 64;
        let upper_tick = get_lower_tick(current_tick, tick_spacing);
        assert_eq!(upper_tick, -6208)
    }
}

#[test]
fn test_swap() {
    let sqrt_price: u128 = 6613869971137543661;
    let current_tick: i32 = -20516;
    let boundary_tick_lower = get_lower_tick(current_tick, 4);
    let liquidity: u128 = 773859267452082;
    let fee_rate: u32 = 400;

    let x_to_y_asii = calculate_swap_orca_clmm(
        sqrt_price, boundary_tick_lower, liquidity, 60_000_000_000,
        fee_rate, true, true
    ).unwrap();

    println!("{x_to_y_asii:?}");

    let x_to_y_not_asii = calculate_swap_orca_clmm(
        sqrt_price, boundary_tick_lower, liquidity, x_to_y_asii.amount_out,
        fee_rate, true, false
    ).unwrap();

    println!("{x_to_y_not_asii:?}");

    let boundary_tick_upper = get_upper_tick(current_tick, 4);

    let y_to_x_asii = calculate_swap_orca_clmm(
        sqrt_price, boundary_tick_upper, liquidity, 30_000_000_000,
        fee_rate, false, true
    ).unwrap();

    println!("{y_to_x_asii:?}");

    let y_to_x_not_asii = calculate_swap_orca_clmm(
        sqrt_price, boundary_tick_upper, liquidity, y_to_x_asii.amount_out,
        fee_rate, false, false
    ).unwrap();

    println!("{y_to_x_not_asii:?}");

    let x_reserves: u128 = 50899997036189;
    let y_reserves: u128 = 6404633224945;

    let x_to_y_asii_amm = calculate_swap_raydium_amm(
        x_reserves, y_reserves, 20_000_000_000, fee_rate,
        true, true
    ).unwrap();

    println!("{x_to_y_asii_amm:?}");

    let x_to_y_not_asii_amm = calculate_swap_raydium_amm(
        x_reserves, y_reserves, x_to_y_asii_amm.amount_out, fee_rate,
        true, false
    ).unwrap();

    println!("{x_to_y_not_asii_amm:?}");

    let y_to_x_asii_amm = calculate_swap_raydium_amm(
        x_reserves, y_reserves, 80_000_000_000, fee_rate,
        false, true
    ).unwrap();

    println!("{y_to_x_asii_amm:?}");

    let y_to_x_not_asii_amm = calculate_swap_raydium_amm(
        x_reserves, y_reserves, y_to_x_asii_amm.amount_out, fee_rate,
        false, false
    ).unwrap();

    println!("{y_to_x_not_asii_amm:?}");
}

#[test]
fn test_sqrt_price_and_active_id() {
    let sqrt_price_from_tick_idx = sqrt_price_from_tick_index(-20240);
    let current_sqrt_price: u128 = 6705669849876714603;
    let tick_idx_from_sqrt_price = tick_index_from_sqrt_price(&6705569693317537905);

    println!("{sqrt_price_from_tick_idx}");
    println!("{current_sqrt_price}");
    println!("{tick_idx_from_sqrt_price}");
}