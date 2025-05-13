export interface SearchSource {
    id: string;
    title: string;
    description?: string;
    url?: string;
    imageUrl?: string;
    type: 'text' | 'image';
    content?: string;
    // Add any other properties that your SearchSource type needs
}
