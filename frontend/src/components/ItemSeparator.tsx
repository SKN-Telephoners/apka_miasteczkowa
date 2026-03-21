import { View, StyleSheet } from "react-native";
import { THEME } from "../utils/constants";


const ItemSeparator = () => {
    return <View style={styles.separator} />;
};

const styles = StyleSheet.create(
    {
        separator: {
            height: 1,
            width: '100%',
            backgroundColor: THEME.colors.lm_ico,
        }
    });

export default ItemSeparator