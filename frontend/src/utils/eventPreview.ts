import { Event, EventPicture } from "../types";

type BuildEventPreviewParams = {
    title: string;
    description: string;
    location: string;
    date: string;
    time: string;
    isPrivate: boolean;
    creatorId: string;
    creatorUsername: string;
    picture?: EventPicture | null;
    pictureUri?: string | null;
    id?: string;
};

export const buildEventPreview = ({
    title,
    description,
    location,
    date,
    time,
    isPrivate,
    creatorId,
    creatorUsername,
    picture,
    pictureUri,
    id = "preview-event",
}: BuildEventPreviewParams): Event => {
    const resolvedPictureUrl = picture?.url ?? pictureUri ?? undefined;

    return {
        id,
        name: title.trim() || "Podgląd wydarzenia",
        description: description.trim(),
        date: date || "--.--.----",
        time: time || "--:--",
        location: location.trim() || "Brak lokalizacji",
        creator_id: creatorId,
        creator_username: creatorUsername,
        created_at: new Date().toISOString(),
        updated_at: undefined,
        is_edited: false,
        comment_count: 0,
        participant_count: 0,
        is_participating: false,
        is_private: isPrivate,
        pictures: resolvedPictureUrl
            ? [{ cloud_id: picture?.cloud_id || "preview-picture", url: resolvedPictureUrl }]
            : undefined,
    };
};