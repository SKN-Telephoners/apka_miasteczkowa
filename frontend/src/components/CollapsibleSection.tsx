import React, { useState, useRef, useEffect, useMemo } from 'react';
import {
    View,
    Text,
    StyleSheet,
    TouchableOpacity,
    ViewStyle,
    Animated,
    LayoutAnimation,
    Platform,
    UIManager
} from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { THEME } from '../utils/constants';
import Icon from 'react-native-vector-icons/Ionicons';
import AppIcon from './AppIcon';

// Enable LayoutAnimation on Android
if (Platform.OS === 'android') {
    if (UIManager.setLayoutAnimationEnabledExperimental) {
        UIManager.setLayoutAnimationEnabledExperimental(true);
    }
}

interface CollapsibleSectionProps {
    title: string;
    children: React.ReactNode;
    initialExpanded?: boolean;
    rightActionIcon?: string;
    onRightActionPress?: () => void;
    style?: ViewStyle;
}

const CollapsibleSection: React.FC<CollapsibleSectionProps> = ({
    title,
    children,
    initialExpanded = false,
    rightActionIcon,
    onRightActionPress,
    style
}) => {
    const { colors } = useTheme();
    const styles = useMemo(() => getStyles(colors), [colors]);

    const [expanded, setExpanded] = useState(initialExpanded);
    const animation = useRef(new Animated.Value(initialExpanded ? 1 : 0)).current;

    const toggleExpand = () => {
        // Prepare for the next frame render
        LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
        setExpanded(!expanded);
    };

    useEffect(() => {
        Animated.timing(animation, {
            toValue: expanded ? 1 : 0,
            duration: 300,
            useNativeDriver: true,
        }).start();
    }, [expanded]);

    const rotateInterpolation = animation.interpolate({
        inputRange: [0, 1],
        outputRange: ['0deg', '180deg']
    });

    return (
        <View style={[styles.container, style]}>
            <View style={styles.headerContainer}>
                <TouchableOpacity
                    style={styles.headerTouch}
                    onPress={toggleExpand}
                    activeOpacity={0.7}
                >
                    <Text style={styles.title}>{title}</Text>
                    <Animated.View style={{ transform: [{ rotate: rotateInterpolation }] }}>
                        <AppIcon name="ArrowDown" size={20} />
                    </Animated.View>
                </TouchableOpacity>

                {rightActionIcon && (
                    <TouchableOpacity
                        style={styles.rightAction}
                        onPress={onRightActionPress}
                        hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                    >
                        <Icon name={rightActionIcon} size={24} color={colors.highlight} />
                    </TouchableOpacity>
                )}
            </View>

            {expanded && (
                <View style={styles.content}>
                    {children}
                </View>
            )}
        </View>
    );
};

const getStyles = (colors: typeof THEME.colors.light) => StyleSheet.create({
    container: {
        marginBottom: THEME.spacing.m,
    },
    headerContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingVertical: THEME.spacing.s,
        borderBottomWidth: 1,
        borderBottomColor: colors.border,
    },
    headerTouch: {
        flex: 1,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
    },
    title: {
        fontSize: 18,
        fontWeight: 'bold',
        color: colors.text,
        marginRight: THEME.spacing.s,
    },
    rightAction: {
        marginLeft: THEME.spacing.m,
        paddingLeft: THEME.spacing.s,
        borderLeftWidth: 1,
        borderLeftColor: colors.border,
    },
    content: {
        paddingTop: THEME.spacing.m,
    }
});

export default CollapsibleSection;
