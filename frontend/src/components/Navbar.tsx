import { TouchableOpacity, View } from "react-native";
import { useTheme } from "../contexts/ThemeContext";
import AppIcon from "./AppIcon";

interface NavbarProps {
  hasNotifications: boolean;
  screenType?: "events" | "map";
  onPress?: () => void;
}

const Navbar = ({ hasNotifications = false, screenType, onPress }: NavbarProps) => {
  const { colors } = useTheme();


  return (
    <View
      style={{ flexDirection: "row", gap: 40, marginRight: 20 }}
      pointerEvents="box-none"
    >
      {screenType === "events" && (
        <TouchableOpacity onPress={onPress}>
          <AppIcon name="Plus" size={28} />
        </TouchableOpacity>
      )}
      <TouchableOpacity onPress={() => ({})}>
        <AppIcon name="Search" size={28} />
      </TouchableOpacity>
      <TouchableOpacity onPress={() => ({})}>
        <AppIcon name="Bell" size={28} />
        {hasNotifications && (
          <View
            style={{
              position: "absolute",
              top: 0,
              right: 0,
              width: 10,
              height: 10,
              borderRadius: 5,
              backgroundColor: colors.highlight,
              borderWidth: 1,
              borderColor: colors.background,
            }}
          />
        )}
      </TouchableOpacity>
    </View>
  );
};

export default Navbar;